FROM python:3.12-slim
WORKDIR /app
COPY infra/placeholders/worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY infra/placeholders/worker/worker.py .
EXPOSE 8001
CMD ["python", "worker.py"]
