import chromadb
import json
from pathlib import Path
from tqdm import tqdm

def update_chunk_topics():
    topics_file = Path("data/micro_test/processed/topics.json")
    if not topics_file.exists():
        print("❌ Topics file not found.")
        return

    print("📖 Loading topics...")
    with open(topics_file, 'r', encoding='utf-8') as f:
        topics = json.load(f)

    # Map topic_id -> list of chunk_ids
    topic_map = {}
    for t_record in topics:
        t_id = t_record['topic_id']
        for c_id in t_record['chunk_ids']:
            topic_map[c_id] = t_id

    print(f"   Mapped {len(topic_map)} chunks to topics.")

    client = chromadb.PersistentClient(path="chroma_db")
    try:
        chunks_col = client.get_collection("micro_chunks_collection")
    except:
        print("❌ micro_chunks_collection not found.")
        return

    print("📥 Fetching current chunk metadata...")
    all_data = chunks_col.get(include=['metadatas'])
    all_ids = all_data['ids']
    all_metas = all_data['metadatas']
    
    # Update logic: iterate through all chunks, check if they have a topic assignment
    ids_to_update = []
    metas_to_update = []
    
    # Assuming order matches (it usually does for .get(), but relying on ids index is safer)
    id_to_meta = {id_: meta for id_, meta in zip(all_ids, all_metas)}

    for c_id, t_id in topic_map.items():
        if c_id in id_to_meta:
            meta = id_to_meta[c_id]
            meta['topic_id'] = t_id
            ids_to_update.append(c_id)
            metas_to_update.append(meta)
    
    if not ids_to_update:
        print("⚠️ No chunks found to update.")
        return

    print(f"🔄 Updating {len(ids_to_update)} chunks with topic IDs...")
    
    batch_size = 100
    for i in tqdm(range(0, len(ids_to_update), batch_size)):
        batch_ids = ids_to_update[i:i+batch_size]
        batch_metas = metas_to_update[i:i+batch_size]
        
        chunks_col.update(
            ids=batch_ids,
            metadatas=batch_metas
        )

    print("✅ Chunks updated with topic IDs.")

if __name__ == "__main__":
    update_chunk_topics()
