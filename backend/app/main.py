from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import auth, history, imagetrace, webgraph

app = FastAPI(title="NetScout API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(webgraph.router, prefix="/api/webgraph", tags=["webgraph"])
app.include_router(imagetrace.router, prefix="/api/imagetrace", tags=["imagetrace"])
app.include_router(history.router, prefix="/api/history", tags=["history"])
