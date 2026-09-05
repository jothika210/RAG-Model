from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.chunking.naive import NaiveChunker
from app.chunking.structure_aware import StructureAwareChunker
from app.config import BASE_DIR, COLLECTIONS
from app.indexing import build_index
from app.routes.admin import router as admin_router
from app.routes.ask import router as ask_router
from app.vectorstore import collection_count


@asynccontextmanager
async def lifespan(app: FastAPI):
    if collection_count(COLLECTIONS["naive"]) == 0:
        build_index(NaiveChunker(), COLLECTIONS["naive"], recreate=True)
    if collection_count(COLLECTIONS["structure_aware"]) == 0:
        build_index(StructureAwareChunker(), COLLECTIONS["structure_aware"], recreate=True)
    yield


app = FastAPI(title="HR Policy RAG", lifespan=lifespan)

app.include_router(ask_router)
app.include_router(admin_router)

app.mount("/", StaticFiles(directory=str(BASE_DIR / "static"), html=True), name="static")
