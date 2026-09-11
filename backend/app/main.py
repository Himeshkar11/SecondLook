from fastapi import FastAPI

app = FastAPI(
    title="SecondLook API",
    description="GeM Bid Compliance API",
)


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
