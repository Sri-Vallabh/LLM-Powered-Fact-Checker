#!/bin/bash
set -e

# Optional: echo for debugging
echo "Running scrape_chroma.py..."
python scrape_chroma.py

echo "Encrypting ChromaDB..."
python encrypt_chroma.py

echo "Decrypting ChromaDB..."
python decrypt_chroma.py

echo "Starting Streamlit app..."
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
