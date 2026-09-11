from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router as api_router

app = FastAPI(
    title="SecondLook API",
    description="GeM Bid Compliance API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
def read_root():
    return {
        "status": "ok",
        "service": "GeM Bid Compliance API",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "GeM Bid Compliance API",
    }
