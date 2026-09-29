from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.rag.retriever import LocalVectorStore

store = LocalVectorStore(ROOT / "app" / "rag" / "knowledge_base", ROOT / "rag_store")
store.build()
print(f"Indexed {len(store.documents)} knowledge-base chunks.")
