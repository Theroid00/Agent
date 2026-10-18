"""Run CPU embedding in its own process so native runtimes stay isolated."""

import contextlib
import json
import sys


def main():
    request = json.load(sys.stdin)
    with contextlib.redirect_stdout(sys.stderr):
        import torch
        from sentence_transformers import SentenceTransformer
        torch.set_num_threads(request['threads'])
        model = SentenceTransformer(request['model'], revision=request['revision'], device='cpu',
                                    cache_folder=request['cache_folder'])
        vectors = model.encode(request['texts'], show_progress_bar=False)
    json.dump(vectors.tolist(), sys.stdout)


if __name__ == '__main__':
    main()
