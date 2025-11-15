"""
FastAPI main application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from cqox.config import settings
from cqox.api.routes import datasets, policies, causal, diagnostics, portfolio, console, upload, visualizations

# Create FastAPI app
app = FastAPI(
    title="CQOx API",
    description="Causal Query Optimizer for Marketing Policy",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(datasets.router, prefix=f"{settings.api_prefix}/datasets", tags=["datasets"])
app.include_router(policies.router, prefix=f"{settings.api_prefix}/policies", tags=["policies"])
app.include_router(causal.router, prefix=f"{settings.api_prefix}/causal", tags=["causal"])
app.include_router(diagnostics.router, prefix=f"{settings.api_prefix}/diagnostics", tags=["diagnostics"])
app.include_router(portfolio.router, prefix=f"{settings.api_prefix}/portfolio", tags=["portfolio"])
app.include_router(console.router, prefix=f"{settings.api_prefix}/console", tags=["console"])
app.include_router(upload.router, prefix=f"{settings.api_prefix}/upload", tags=["upload"])
app.include_router(visualizations.router, prefix=f"{settings.api_prefix}/visualizations", tags=["visualizations"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "CQOx API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
