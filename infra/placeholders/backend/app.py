from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

app = FastAPI(title="Rustbucket Placeholder Backend")

request_count = 0


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/api/ping")
def ping():
    return {
        "message": "pong",
        "service": "rustbucket-placeholder-backend"
    }


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    global request_count
    request_count += 1

    return f"""# HELP rustbucket_requests_total Total requests
# TYPE rustbucket_requests_total counter
rustbucket_requests_total {request_count}
"""