"""Local multilingual article embeddings; no Gemini or SerpApi requests."""
import argparse
import hashlib
import json
from pathlib import Path

from collect_paa import read_json, write_json, now

ROOT = Path(__file__).resolve().parents[1]


def normalized(vector):
    import numpy as np
    value = np.asarray(vector, dtype=np.float32)
    length = float(np.linalg.norm(value))
    if not length:
        raise ValueError('Embedding kosong tidak boleh menjadi skor semantik.')
    return value / length


class LocalEmbeddings:
    def __init__(self, config, root=ROOT):
        self.config = config
        self.root = root
        self.model = None
        self.tokenizer = None
        self.identity = {
            'model': config['embedding_model'],
            'chunk_tokens': config['embedding_chunk_tokens'],
            'chunk_overlap': config['embedding_chunk_overlap'],
            'aggregation': config['embedding_aggregation'],
            'implementation': 'fastembed_onnx_mean_chunks_v1',
        }
        self.cache = root / config['embedding_cache']
        self.cache.mkdir(parents=True, exist_ok=True)

    def load(self):
        if self.model is not None:
            return
        from fastembed import TextEmbedding
        from tokenizers import Tokenizer
        self.model = TextEmbedding(
            model_name=self.config['embedding_model'],
            cache_dir=str(self.root / self.config['embedding_model_cache']),
            threads=self.config.get('embedding_threads', 2),
            providers=['CPUExecutionProvider'],
        )
        # Clone tokenizer before disabling truncation; leave inference tokenizer intact.
        self.tokenizer = Tokenizer.from_str(self.model.model.tokenizer.to_str())
        self.tokenizer.no_truncation()
        self.tokenizer.no_padding()

    def vector(self, text, kind):
        import numpy as np
        if kind not in {'query', 'article'} or not text.strip():
            raise ValueError('Jenis atau teks embedding tidak valid.')
        key = hashlib.sha256(json.dumps(
            [self.identity, kind, text], ensure_ascii=False, sort_keys=True
        ).encode('utf-8')).hexdigest()
        path = self.cache / (key + '.json')
        if path.exists():
            result = read_json(path)
            return np.asarray(result['vector'], dtype=np.float32), result
        self.load()
        ids = self.tokenizer.encode(text, add_special_tokens=False).ids
        size = self.config['embedding_chunk_tokens']
        overlap = self.config['embedding_chunk_overlap']
        if not 0 <= overlap < size <= 112:
            raise ValueError('Chunk harus <=112 token, dengan overlap lebih kecil dari chunk.')
        chunks = []
        for start in range(0, len(ids), size - overlap):
            chunks.append(self.tokenizer.decode(ids[start:start + size]))
            if start + size >= len(ids):
                break
        # This MiniLM model needs no query/passage prefix; all text is represented.
        vectors = [normalized(v) for v in self.model.embed(chunks, batch_size=8)]
        result_vector = normalized(np.mean(vectors, axis=0))
        result = {
            **self.identity, 'text_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
            'kind': kind, 'n_chunks': len(chunks), 'n_tokens': len(ids),
            'dimension': len(result_vector), 'vector': result_vector.tolist(),
            'computed_at': now(),
        }
        write_json(path, result)
        return result_vector, result

    def fingerprint(self):
        """Persist exact downloaded artifacts, including HF snapshot when available."""
        base = self.root / self.config['embedding_model_cache']
        artifacts = []
        if base.exists():
            for path in sorted(base.rglob('*')):
                if path.is_file() and path.suffix in {'.onnx', '.json'} and path.name != 'artifact_manifest.json':
                    h = hashlib.sha256()
                    with path.open('rb') as stream:
                        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                            h.update(chunk)
                    artifacts.append({'path': str(path.relative_to(self.root)), 'sha256': h.hexdigest()})
        return {'identity': self.identity, 'artifacts': artifacts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/article_features.json')
    parser.add_argument('--download-model', action='store_true')
    args = parser.parse_args()
    if not args.download_model:
        print('Tambahkan --download-model untuk mengunduh model embedding lokal.')
        return
    engine = LocalEmbeddings(read_json(args.config))
    engine.load()
    write_json(engine.root / engine.config['embedding_model_cache'] / 'artifact_manifest.json', engine.fingerprint())
    print('Model embedding siap; tidak ada token Gemini atau kuota SerpApi terpakai.')


if __name__ == '__main__':
    main()
