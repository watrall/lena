from fastapi import FastAPI

app = FastAPI(title="LENA Backend", version="0.1.0")


@app.get("/healthz")
def healthcheck() -> dict[str, bool]:
    """Basic readiness probe for infrastructure integrations."""
    return {"ok": True}
