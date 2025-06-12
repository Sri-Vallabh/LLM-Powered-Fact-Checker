FROM python:3.11-slim

WORKDIR /app

ENV HF_HOME=/data/hf_cache
ENV TRANSFORMERS_CACHE=/data/hf_cache/transformers
ENV HF_DATASETS_CACHE=/data/hf_cache/datasets
ENV HF_HUB_CACHE=/data/hf_cache/hub

RUN mkdir -p /data/hf_cache/transformers /data/hf_cache/datasets /data/hf_cache/hub && chmod -R 777 /data/hf_cache

# Ensure /app is writable
RUN chmod -R 777 /app
RUN mkdir -p /app/chroma_db && chmod -R 777 /app/chroma_db

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Add spaCy model download
RUN python -m spacy download en_core_web_sm  # Critical fix [1][2]

COPY . .

RUN chmod +x /app/entrypoint.sh
RUN mkdir -p /app/data && chmod -R 777 /app/data

EXPOSE 8501

ENTRYPOINT ["/app/entrypoint.sh"]
