from app.retrieval import split_text

def test_split_text_returns_chunks():
    chunks = split_text("This is sentence one. This is sentence two. " * 100, chunk_size=120, overlap=20)
    assert len(chunks) > 1
    assert all(chunks)
