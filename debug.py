import chromadb
from chromadb.utils import embedding_functions

# Adjust these as needed
CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "pib_titles"

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_collection(
    name=COLLECTION_NAME,
    embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
)

# Retrieve all documents and metadata (ids are always returned)
all_docs = collection.get(include=["documents", "metadatas"])

print("Total documents:", len(all_docs["ids"]))
for i, (doc_id, doc, meta) in enumerate(zip(all_docs["ids"], all_docs["documents"], all_docs["metadatas"])):
    print(f"\n--- Document {i+1} ---")
    print("ID:", doc_id)
    print("Document:", doc)
    print("Metadata:", meta)
