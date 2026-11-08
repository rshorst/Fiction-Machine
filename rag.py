import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings
from sentence_transformers import SentenceTransformer
from datetime import datetime

model = SentenceTransformer('all-MiniLM-L6-v2')

class LocalEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        return model.encode(input).tolist()

embedding_fn = LocalEmbeddingFunction()

import config

client = config.chroma_client()

miranda_papers = client.get_or_create_collection(
    name="miranda_papers",
    embedding_function=embedding_fn,
    metadata={"description": "Theory, research, fragments, provocations. Strange, unresolved, resistant to reduction."}
)

voices = client.get_or_create_collection(
    name="voices",
    embedding_function=embedding_fn,
    metadata={"description": "Rachel's writing. Opinion, commitment, the particular way she sees."}
)

def deposit(collection, text, source, provenance, tags=None):
    doc_id = f"{source}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    collection.add(
        documents=[text],
        ids=[doc_id],
        metadatas=[{
            "source": source,
            "provenance": provenance,
            "deposited": datetime.now().isoformat(),
            "tags": ",".join(tags) if tags else "",
        }]
    )
    return doc_id

def reach(collection, query, n=3):
    results = collection.query(
        query_texts=[query],
        n_results=n
    )
    return results

def reach_both(query, n=2):
    return {
        "miranda_papers": reach(miranda_papers, query, n=n),
        "voices": reach(voices, query, n=n)
    }

if __name__ == "__main__":
    print(f"miranda_papers: {miranda_papers.count()} documents")
    print(f"voices: {voices.count()} documents")
