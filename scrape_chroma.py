import os
import requests
from bs4 import BeautifulSoup
import chromadb
from chromadb.utils import embedding_functions
import gc
import csv

# === CONFIGURATION ===
CHROMA_PATH = "app/chroma_db"
COLLECTION_NAME = "pib_titles"

def save_titles_to_csv(titles, filename="pib_titles.csv"):
    with open(filename, mode="w", newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["title", "source"])  # header
        for title, source in titles:
            writer.writerow([title, source])
    print(f"Saved {len(titles)} titles to {filename}")

def scrape_and_store():
    RSS_URLS = [
        "https://www.pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3",
        "https://www.pib.gov.in/RssMain.aspx?ModId=8&Lang=1&Regid=3"
    ]

    all_titles_sources = set()
    for url in RSS_URLS:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "xml")
            items = soup.find_all("item")
            for item in items:
                title_tag = item.find("title")
                link_tag = item.find("link")
                if title_tag and title_tag.text and link_tag and link_tag.text:
                    all_titles_sources.add((title_tag.text.strip(), link_tag.text.strip()))
        except Exception as e:
            print(f"Error fetching {url}: {e}")

    all_titles_sources = list(all_titles_sources)
    print(f"Fetched {len(all_titles_sources)} unique titles.")

    # Save to CSV
    save_titles_to_csv(all_titles_sources, filename="data/pib_titles.csv")


    # Prepare for ChromaDB
    documents = [title for title, source in all_titles_sources]
    metadatas = [{"source": source} for title, source in all_titles_sources]
    ids = [f"title_{i}" for i in range(len(all_titles_sources))]

    # Store in ChromaDB
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
    )
    collection.add(documents=documents, ids=ids, metadatas=metadatas)

    # Explicitly close client
    del collection
    del client
    gc.collect()

if __name__ == "__main__":
    scrape_and_store()
    print("Scraping complete. ChromaDB ready for encryption.")
