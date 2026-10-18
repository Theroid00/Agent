"""CPU FAISS cosine retrieval with a separate allowed-ID set per finding."""

import json
import html
import re
from pathlib import Path
import subprocess
import sys
import numpy as np
import faiss
from rank_bm25 import BM25Okapi
from .config import CONFIG

STOPWORDS = {'a', 'an', 'and', 'as', 'at', 'by', 'for', 'from', 'in', 'into', 'is',
             'of', 'on', 'or', 'the', 'to', 'with'}


def expand_query(query):
    additions = []
    lower = query.lower()
    if re.search(r'\b(?:many|multiple|distinct)\b.*\bports?\b', lower):
        additions.append('network port scanning')
    if 'outbound' in lower and re.search(r'\b(?:data|transfer|traffic|bytes)\b', lower):
        additions.append('data exfiltration')
    return query + (' ' + ' '.join(additions) if additions else '')


def _lexical_tokens(text):
    words = re.findall(r'[a-z0-9]+', text.lower())
    # shortcut: plural-only normalization; use a full stemmer if retrieval tests require it.
    return [word[:-1] if len(word) > 4 and word.endswith('s') and not word.endswith('ss') else word
            for word in words if word not in STOPWORDS]


def _encoder(*, query=False):
    def encode(texts):
        if query:
            texts = [CONFIG['rag'].get('query_prefix', '') + text for text in texts]
        request = {'model': CONFIG['embed_model'], 'revision': CONFIG['embed_revision'],
                   'threads': CONFIG['embedding_threads'], 'texts': texts,
                   'cache_folder': str((Path(CONFIG['paths']['cache']) / 'models').resolve())}
        # PyTorch and FAISS wheels can ship competing OpenMP runtimes on macOS.
        completed = subprocess.run([sys.executable, str(Path(__file__).with_name('_embedding_worker.py'))],
                                   input=json.dumps(request), capture_output=True, text=True)
        if completed.returncode:
            raise RuntimeError(f'Embedding worker failed ({completed.returncode}): {completed.stderr[-2000:]}')
        return json.loads(completed.stdout)
    return encode


class AttackRAG:
    def __init__(self, techniques, *, encoder=None, source_ref):
        faiss.omp_set_num_threads(CONFIG['embedding_threads'])
        if not techniques:
            raise ValueError("Cannot index an empty technique catalog")
        self.techniques = techniques
        self.ids = sorted(techniques)
        self.source_ref = source_ref
        self.encoder = encoder or _encoder()
        self.query_encoder = encoder or _encoder(query=True)
        self.retrieval_log = {}
        self.documents = [self._document(techniques[tid]) for tid in self.ids]
        vectors = self._encode(self.documents)
        self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)
        self.bm25 = BM25Okapi([_lexical_tokens(text) for text in self.documents])

    @staticmethod
    def _document(record):
        def clean(text, bound):
            text = re.sub(r'\(Citation:[^)]*\)', '', text)
            text = re.sub(r'\[([^]]+)\]\([^)]+\)', r'\1', text)
            text = html.unescape(re.sub(r'<[^>]+>', ' ', text))
            return ' '.join(text.split())[:bound]
        description = clean(record['description'], CONFIG['rag']['description_chars'])
        detection = clean(record.get('detection', ''), CONFIG['rag']['detection_chars'])
        return f"{record['id']} {record['name']}. Detection: {detection} Description: {description}"

    def _encode(self, texts, *, query=False):
        encoder = self.query_encoder if query else self.encoder
        vectors = np.asarray(encoder(texts), dtype="float32").copy(order="C")
        if vectors.ndim != 2 or vectors.shape[0] != len(texts) or not np.isfinite(vectors).all():
            raise ValueError("Encoder returned invalid vectors")
        if np.any(np.linalg.norm(vectors, axis=1) == 0):
            raise ValueError("Encoder returned zero vectors")
        faiss.normalize_L2(vectors)
        return vectors

    def search(self, query, *, k, finding_id):
        if not isinstance(k, int) or k < 1:
            raise ValueError("k must be a positive integer")
        if not query.strip() or not finding_id:
            raise ValueError("Query and finding_id are required")
        query = expand_query(query)
        scores, positions = self.index.search(self._encode([query], query=True), len(self.ids))
        cosine = {int(position): float(score) for score, position in zip(scores[0], positions[0])}
        order = [int(position) for position in positions[0]]
        fused = {}
        if CONFIG['rag']['hybrid']:
            constant = CONFIG['rag']['rrf_k']
            fused = {position: 1 / (constant + rank) for rank, position in enumerate(order, 1)}
            lexical_scores = self.bm25.get_scores(_lexical_tokens(query))
            lexical_order = sorted(range(len(self.ids)), key=lambda i: (-lexical_scores[i], self.ids[i]))
            positive = [position for position in lexical_order if lexical_scores[position] > 0]
            for rank, position in enumerate(positive, 1):
                fused[position] += 1 / (constant + rank)
            order.sort(key=lambda position: (-fused[position], self.ids[position]))
        results = []
        for position in order[:min(k, len(self.ids))]:
            tid = self.ids[int(position)]
            record = self.techniques[tid]
            results.append({"id": tid, "name": record["name"], "tactics": record["tactics"],
                            "snippet": self._document(record), "score": cosine[position],
                            "rank_score": fused.get(position, cosine[position])})
            self.retrieval_log.setdefault(finding_id, set()).add(tid)
        return results

    def get_technique(self, technique_id, *, finding_id):
        if technique_id not in self.retrieval_log.get(finding_id, set()):
            raise ValueError("Technique was not retrieved for this finding")
        return self.techniques[technique_id]

    def save(self, path):
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(path / "attack.faiss"))
        (path / "metadata.json").write_text(json.dumps({
            "source_ref": self.source_ref, "model": CONFIG["embed_model"], "model_revision": CONFIG['embed_revision'],
            "document_settings": {key: CONFIG['rag'][key] for key in ['document_format', 'description_chars', 'detection_chars', 'query_prefix']},
            "ids": self.ids, "techniques": self.techniques,
        }, indent=2))

    @classmethod
    def load(cls, path, *, encoder=None, expected_source_ref):
        faiss.omp_set_num_threads(CONFIG['embedding_threads'])
        path = Path(path)
        meta = json.loads((path / "metadata.json").read_text())
        if (meta["source_ref"] != expected_source_ref or meta["model"] != CONFIG["embed_model"]
                or meta.get('model_revision') != CONFIG['embed_revision']):
            raise ValueError("Index source/model does not match configuration")
        if meta.get('document_settings') != {key: CONFIG['rag'][key] for key in ['document_format', 'description_chars', 'detection_chars', 'query_prefix']}:
            raise ValueError('Index document settings do not match configuration')
        obj = cls.__new__(cls)
        obj.ids, obj.techniques, obj.source_ref = meta["ids"], meta["techniques"], meta["source_ref"]
        obj.encoder, obj.retrieval_log = encoder or _encoder(), {}
        obj.query_encoder = encoder or _encoder(query=True)
        obj.documents = [obj._document(obj.techniques[tid]) for tid in obj.ids]
        obj.index = faiss.read_index(str(path / "attack.faiss"))
        obj.bm25 = BM25Okapi([_lexical_tokens(text) for text in obj.documents])
        if obj.index.ntotal != len(obj.ids) or len(set(obj.ids)) != len(obj.ids):
            raise ValueError("Index metadata is corrupt")
        return obj
