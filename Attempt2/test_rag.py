import os
from rag_pipeline import RAGPipeline

def run_rag_query():
    # Initialize pipeline
    pipeline = RAGPipeline(
        db_path="data/test_db",
        model_dir="models"
    )
    
    print("\nTesting query...")
    try:
        response = pipeline.query("Who is Lord Chaitanya?", collection_name="test_collection")
        
        if isinstance(response, dict) and "answer" in response:
            print("\n🤖 RESPONSE:")
            print(response["answer"])
            print("\n📚 SOURCES:")
            for i, doc in enumerate(response["source_documents"]):
                meta = response["source_metadata"][i]
                print(f"- [{meta.get('title', 'Unknown')}] {doc[:100]}...")
        else:
            print(f"Query Response: {response}")
            
    except Exception as e:
        print(f"Error querying: {e}")
        print("Make sure you have run test_ingestion.py and the embedding model is available.")

if __name__ == "__main__":
    run_rag_query()
