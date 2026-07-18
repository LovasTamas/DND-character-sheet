from fastapi import FastAPI

from app.database.db import Base, engine
from app.api import characters

# Phase 1: create tables directly. Swap for Alembic migrations once schema stabilizes.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="D&D 2024 Character Manager")

app.include_router(characters.router)


@app.get("/health")
def health():
    return {"status": "ok"}
