import os
import json
from typing import List, Dict
from tools.song_chunker import SongChunker
from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

class ExpertRAGPipeline:
    def __init__(self, db_path: str = "Attempt2/data/db"):
        self.db_path = db_path
        self.song_chunker = SongChunker()
        self.db = chromadb.PersistentClient(path=db_path)
        
    def ingest_songs(self, songs_dir: str):
        all_chunks = []
        for root, _, files in os.walk(songs_dir):
            for file in files:
                if file.endswith(".txt"):
                    file_path = os.path.join(root, file)
                    # Use the directory name as a category/book_id
                    book_id = os.path.basename(root)
                    chunks = self.song_chunker.chunk_song(file_path, metadata_ext={"book_id": book_id})
                    all_chunks.extend(chunks)
        
        # Save processed chunks to jsonl for inspection
        os.makedirs("Attempt2/data/processed", exist_ok=True)
        with open("Attempt2/data/processed/songs_chunks.jsonl", "w", encoding="utf-8") as f:
            for chunk in all_chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + "
")
                
        print(f"Ingested {len(all_chunks)} chunks from {songs_dir}")
        return all_chunks

    def create_index(self, chunks: List[Dict], collection_name: str = "expert_rag"):
        chroma_collection = self.db.get_or_create_collection(collection_name)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        documents = []
        for chunk in chunks:
            doc = Document(
                text=chunk["text"],
                doc_id=chunk["id"],
                metadata=chunk["metadata"]
            )
            documents.append(doc)
            
        index = VectorStoreIndex.from_documents(
            documents, 
            storage_context=storage_context,
            # We'll configure models here later
        )
        return index

if __name__ == "__main__":
    pipeline = ExpertRAGPipeline()
    # pipeline.ingest_songs("Attempt2/gaudiya_gitanjali")
