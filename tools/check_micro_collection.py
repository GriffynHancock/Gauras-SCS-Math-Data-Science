import chromadb

def check_collection():
    client = chromadb.PersistentClient(path="chroma_db")
    try:
        collection = client.get_collection("micro_chunks_collection")
        print(f"✅ Collection count: {collection.count()}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_collection()
