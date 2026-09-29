from pathlib import Path
from dataclasses import dataclass

@dataclass
class DocumentChunk:
    text: str
    source: str
    version: str
    chunk_id: str

def load_documents(kb_dir: Path) -> list[DocumentChunk]:
    docs = []
    for path in sorted(kb_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        version = "unknown"
        parts = []
        for paragraph in text.split("\n\n"):
            paragraph = paragraph.strip()
            if not paragraph or paragraph.startswith("# "):
                continue
            if paragraph.lower().startswith("policy version:"):
                version = paragraph.split(":", 1)[1].strip()
                continue
            parts.append(paragraph)
        if parts:
            docs.append(DocumentChunk(" ".join(parts), path.name, version, path.stem))
    return docs
