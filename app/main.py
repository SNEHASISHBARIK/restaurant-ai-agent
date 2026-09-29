from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.api.orders import router as orders_router
from app.api.tickets import router as tickets_router
from app.api.chat import router as chat_router
from app.database.database import init_db, SessionLocal
from app.database.seed import seed_orders
from app.rag.retriever import LocalVectorStore
from app.utils.config import get_settings
from app.utils.logger import configure_logging

ROOT=Path(__file__).resolve().parents[1]

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(get_settings().log_level)
    init_db()
    db=SessionLocal()
    try: seed_orders(db)
    finally: db.close()
    LocalVectorStore(ROOT/"app"/"rag"/"knowledge_base", ROOT/"rag_store").load()
    yield

app=FastAPI(title="Restaurant Support Agent", version="1.0.0", description="Minimal AI restaurant support and operations agent.", lifespan=lifespan)
app.include_router(orders_router)
app.include_router(tickets_router)
app.include_router(chat_router)
app.mount("/static", StaticFiles(directory=str(ROOT/"app"/"static")), name="static")

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home():
    return (ROOT/"app"/"static"/"index.html").read_text(encoding="utf-8")

@app.get("/health", tags=["system"])
def health():
    return {"status":"ok"}
