from pathlib import Path
from app.rag.retriever import LocalVectorStore

def test_rag_retrieval(tmp_path):
    root=Path(__file__).resolve().parents[1]
    store=LocalVectorStore(root/'app'/'rag'/'knowledge_base', tmp_path/'store'); store.build()
    results=store.search('What is the refund policy?')
    assert results and results[0]['source']=='refund_policy.md'

def test_rag_unknown(tmp_path):
    root=Path(__file__).resolve().parents[1]
    store=LocalVectorStore(root/'app'/'rag'/'knowledge_base', tmp_path/'store'); store.build()
    assert store.search('Who is the prime minister of Canada?') == []
