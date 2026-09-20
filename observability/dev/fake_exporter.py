"""Fake Rustbucket exporter for developing Prometheus and Grafana.

Publishes the exact metric names from Section 2.7 with moving numbers.

  python fake_exporter.py --mode backend --port 8000
  python fake_exporter.py --mode worker --port 8001
"""
import argparse
import random
import threading
import time

from prometheus_client import Counter, Gauge, Histogram, start_http_server

# (handler, method, [(status, weight), ...])
BACKEND_ROUTES = [
    ("/api/scans", "POST", [("202", 85), ("400", 10), ("500", 5)]),
    ("/api/scans/{scan_id}", "GET", [("200", 96), ("500", 4)]),
    ("/api/repos", "GET", [("200", 98), ("500", 2)]),
]


def run_backend():
    requests_total = Counter(
        "http_requests_total", "Total HTTP requests", ["handler", "method", "status"]
    )
    duration = Histogram(
        "http_request_duration_seconds",
        "HTTP request latency in seconds",
        ["handler", "method"],
        buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
    )
    queue = Gauge("rustbucket_queue_length", "Number of jobs waiting in Redis")

    # Create every series at 0 so all of them show up immediately.
    for handler, method, statuses in BACKEND_ROUTES:
        duration.labels(handler, method)
        for status, _ in statuses:
            requests_total.labels(handler, method, status)

    queue_len = 0
    while True:
        for handler, method, statuses in BACKEND_ROUTES:
            codes = [s for s, _ in statuses]
            weights = [w for _, w in statuses]
            for _ in range(random.randint(0, 4)):
                status = random.choices(codes, weights=weights)[0]
                requests_total.labels(handler, method, status).inc()
                base = 0.15 if method == "POST" else 0.05
                duration.labels(handler, method).observe(random.lognormvariate(0, 0.6) * base)
        queue_len = max(0, min(15, queue_len + random.choice([-2, -1, 0, 1, 2])))
        queue.set(queue_len)
        time.sleep(1)


def run_worker():
    started = Counter("rustbucket_scans_started_total", "Scans started")
    completed = Counter("rustbucket_scans_completed_total", "Scans completed")
    failed = Counter("rustbucket_scans_failed_total", "Scans failed")
    duration = Histogram(
        "rustbucket_scan_duration_seconds",
        "Scan duration in seconds",
        buckets=(5, 10, 20, 30, 45, 60, 90, 120),
    )

    while True:
        if random.random() < 0.2:  # about 12 scans per minute
            started.inc()
            seconds = min(90.0, max(5.0, random.gauss(30, 18)))
            duration.observe(seconds)
            if random.random() < 0.9:
                completed.inc()
            else:
                failed.inc()
        time.sleep(1)


def main():
    parser = argparse.ArgumentParser(description="Fake Rustbucket metrics exporter")
    parser.add_argument("--mode", choices=["backend", "worker"], required=True)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    start_http_server(args.port)
    target = run_backend if args.mode == "backend" else run_worker
    threading.Thread(target=target, daemon=True).start()
    print(f"Fake {args.mode} exporter on http://localhost:{args.port}/metrics")
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()