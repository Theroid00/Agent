"""T-RAG: cosine search, bounded results, per-finding grounding and disk state."""

import math
import pytest
from cyberagents.rag import AttackRAG


def test_normalizes_vectors_before_inner_product(techniques, fake_encoder):
    rag = AttackRAG(techniques, encoder=fake_encoder, source_ref="fixture")
    results = rag.search("ssh", k=3, finding_id="f1")
    assert [r["id"] for r in results] == ["T1110.001", "T1190", "T1046"]
    assert math.isclose(results[0]["score"], 1.0, abs_tol=1e-6)
    assert math.isclose(results[1]["score"], math.sqrt(0.5), abs_tol=1e-6)
    assert {"id", "name", "tactics", "snippet"} <= results[0].keys()


def test_retrieval_log_is_per_finding_and_accumulates(techniques, fake_encoder):
    rag = AttackRAG(techniques, encoder=fake_encoder, source_ref="fixture")
    rag.search("ssh", k=1, finding_id="f1")
    rag.search("scan", k=1, finding_id="f2")
    assert set(rag.retrieval_log["f1"]) == {"T1110.001"}
    assert set(rag.retrieval_log["f2"]) == {"T1046"}
    rag.search("scan", k=1, finding_id="f1")
    assert set(rag.retrieval_log["f1"]) == {"T1110.001", "T1046"}


def test_get_technique_rejects_cross_finding_or_memory_ids(techniques, fake_encoder):
    rag = AttackRAG(techniques, encoder=fake_encoder, source_ref="fixture")
    rag.search("ssh", k=1, finding_id="f1")
    assert rag.get_technique("T1110.001", finding_id="f1")["name"] == "Password Guessing"
    with pytest.raises(ValueError, match="retriev"):
        rag.get_technique("T1046", finding_id="f1")
    with pytest.raises(ValueError, match="retriev"):
        rag.get_technique("T1110.001", finding_id="f2")


@pytest.mark.parametrize("k", [0, -1])
def test_rejects_invalid_k(techniques, fake_encoder, k):
    rag = AttackRAG(techniques, encoder=fake_encoder, source_ref="fixture")
    with pytest.raises(ValueError, match="k"):
        rag.search("ssh", k=k, finding_id="f1")


def test_k_larger_than_corpus_does_not_duplicate_last_id(techniques, fake_encoder):
    rag = AttackRAG(techniques, encoder=fake_encoder, source_ref="fixture")
    results = rag.search("ssh", k=8, finding_id="f1")
    assert len(results) == len(techniques)
    assert len({r["id"] for r in results}) == len(techniques)


def test_index_round_trip_keeps_id_order_and_checks_source(techniques, fake_encoder, tmp_path):
    rag = AttackRAG(techniques, encoder=fake_encoder, source_ref="fixture")
    rag.save(tmp_path)
    loaded = AttackRAG.load(tmp_path, encoder=fake_encoder, expected_source_ref="fixture")
    assert loaded.search("ssh", k=1, finding_id="fresh")[0]["id"] == "T1110.001"
    assert "f1" not in loaded.retrieval_log
    with pytest.raises(ValueError, match="source"):
        AttackRAG.load(tmp_path, encoder=fake_encoder, expected_source_ref="other")


@pytest.mark.slow
def test_real_configured_retrieval_meets_plan_threshold():
    import importlib.util
    if importlib.util.find_spec('sentence_transformers') is None or importlib.util.find_spec('torch') is None:
        pytest.skip('Install requirements.txt to run actual semantic retrieval')
    from cyberagents.pipeline import check_retrieval
    report = check_retrieval()
    assert report['total'] == 6
    assert report['passed'] >= 5


def test_index_rejects_stale_document_configuration(techniques, fake_encoder, tmp_path, monkeypatch):
    from cyberagents.config import CONFIG
    rag = AttackRAG(techniques, encoder=fake_encoder, source_ref='fixture')
    rag.save(tmp_path)
    monkeypatch.setitem(CONFIG['rag'], 'document_format', 'changed-format')
    with pytest.raises(ValueError, match='document'):
        AttackRAG.load(tmp_path, encoder=fake_encoder, expected_source_ref='fixture')


def test_hybrid_recovers_a_lexical_match_when_dense_vectors_disagree(techniques, monkeypatch):
    from cyberagents.config import CONFIG
    monkeypatch.setitem(CONFIG['rag'], 'hybrid', True)
    def misleading_encoder(texts):
        return [[0., 1.] if text.startswith('T1046 ') else [1., 0.] for text in texts]
    rag = AttackRAG(techniques, encoder=misleading_encoder, source_ref='fixture')
    assert rag.search('port scan', k=1, finding_id='f1')[0]['id'] == 'T1046'


def test_query_normalization_preserves_input_and_never_inserts_technique_ids():
    import re
    from cyberagents.rag import expand_query
    query = 'rapid connections to multiple destination ports'
    expanded = expand_query(query)
    assert expanded.startswith(query) and len(expanded) > len(query)
    assert not re.search(r'\bT\d{4}', expanded)
    assert expand_query('ordinary application health check') == 'ordinary application health check'
