import re
from sqlalchemy import select
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.models import TranscriptChunk
from app.config import settings

def retrieve(db: Session, query: str) -> list[dict]:
    chunks = list(db.scalars(select(TranscriptChunk)))
    if not chunks:
        return []
    corpus = [c.content for c in chunks]
    try:
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        matrix = vectorizer.fit_transform(corpus + [query])
        scores = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
    except ValueError:
        return []
    ranked = sorted(zip(chunks, scores), key=lambda x: float(x[1]), reverse=True)
    results = []
    for chunk, score in ranked[:settings.retrieval_top_k]:
        if float(score) < settings.min_retrieval_score:
            continue
        results.append({
            "source": chunk.source_name,
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
            "score": round(float(score), 4)
        })
    return results

def split_text(text: str, chunk_size: int = 1400, overlap: int = 200) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    chunks, start = [], 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            boundary = text.rfind(". ", start + chunk_size // 2, end)
            if boundary > start:
                end = boundary + 1
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks
