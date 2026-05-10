FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY api-requirements.txt .
RUN pip install --no-cache-dir -r api-requirements.txt

# Cache the embedding model at build time so cold starts are fast
ENV SENTENCE_TRANSFORMERS_HOME=/app/.cache/st
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY . .

EXPOSE 7860

CMD ["sh", "-c", "python rag/setup.py && uvicorn api.server:app --host 0.0.0.0 --port 7860"]
