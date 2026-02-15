import os
import sys
from pathlib import Path
from fastmcp import FastMCP

# Ensure absolute paths for Jan.ai/MCP context
SCRIPT_DIR = Path(__file__).parent.absolute()
DB_PATH = str(SCRIPT_DIR / "test_run_1" / "db")
MODEL_DIR = str(SCRIPT_DIR / "models")

# Add current dir to sys.path to ensure local imports work
sys.path.append(str(SCRIPT_DIR))

from rag_pipeline import RAGPipeline

# Initialize the MCP server
mcp = FastMCP("Gaudiya Vaishnava RAG")

# Initialize RAG Pipeline lazily or at startup
# We'll initialize it once to keep it in memory
print(f"Initializing RAG Pipeline with DB: {DB_PATH}")
rag = RAGPipeline(db_path=DB_PATH, model_dir=MODEL_DIR)

@mcp.tool()
def gaudiya_rag_query(question: str, synthesize: bool = True) -> str:
    """
    Query the Gaudiya Vaishnava RAG system for theological information.
    
    Args:
        question: The theological or historical question to ask.
        synthesize: Whether to synthesize a cohesive answer or just return raw sources.
    """
    try:
        # We use the collection from test_run_1
        result = rag.query(
            question, 
            collection_name="test_run_1_collection",
            n_initial=15,
            n_final=5,
            synthesize=synthesize
        )
        
        if synthesize:
            if isinstance(result, str):
                return f"Error: {result}"
            
            answer = result.get('answer', 'No answer generated.')
            sources_list = []
            for i in range(len(result.get("source_documents", []))):
                meta = result["source_metadata"][i]
                title = meta.get('title', 'Unknown')
                author = meta.get('author', 'Unknown')
                sources_list.append(f"- {title} by {author}")
            
            sources_str = "
".join(sources_list)
            return f"{answer}

Sources:
{sources_str}"
        else:
            # Return JSON-like string of raw results
            import json
            return json.dumps(result, indent=2, ensure_ascii=False)
            
    except Exception as e:
        return f"Error executing query: {str(e)}"

if __name__ == "__main__":
    # Run the server using stdio transport
    mcp.run()
