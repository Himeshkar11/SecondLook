from fastapi import FastAPI

from app.api.router import router as api_router

app = FastAPI(
    title="SecondLook API",
    description="GeM Bid Compliance API",
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
