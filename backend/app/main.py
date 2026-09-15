from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings
from app.api.routes import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.database import init_db
    await init_db()
    yield


app = FastAPI(
    title="Cost-Aware Multi-Tier Cascading Router API",
    description="Intelligent LLM Router with Confidence Gates, Dynamic Escalation, and Cost Audit Ledger.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for development & local Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {
        "service": "Cost-Aware Cascading LLM Router API",
        "status": "healthy",
        "docs_url": "/docs",
        "api_prefix": "/api"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
