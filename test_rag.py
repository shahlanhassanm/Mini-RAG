import os
import sys
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
try:
    from langchain_ollama import ChatOllama
except ImportError:
    from langchain_community.chat_models import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load env variables
load_dotenv()

INDEX_DIR = "faiss_index"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

def get_llm():
    llm_type = os.getenv("LLM_TYPE", "openrouter").lower()
    
    if llm_type == "ollama":
        model_name = os.getenv("OLLAMA_MODEL", "llama3.2")
        print(f"Using Local Ollama model: {model_name}")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return ChatOllama(model=model_name, base_url=base_url)
    
    elif llm_type == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("Warning: OPENROUTER_API_KEY not found. LLM generation will be skipped.")
            return None
        model_name = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3-8b-instruct:free")
        print(f"Using OpenRouter model: {model_name}")
        return ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            model=model_name
        )
    return None

def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])

def run_test_query(query, vector_store, llm, prompt):
    print(f"\nQUERY: '{query}'")
    
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})
    
    print("Retrieving context...")
    retrieved_docs = retriever.invoke(query)
    
    print("-" * 20 + " RETRIEVED CONTEXT " + "-" * 20)
    if not retrieved_docs:
        print("No relevant documents found.")
    
    for i, doc in enumerate(retrieved_docs):
        source = os.path.basename(doc.metadata.get('source', 'Unknown'))
        content_preview = doc.page_content.replace('\n', ' ')[:200]
        print(f"Chunk {i+1} [{source}]: {content_preview}...")
    print("-" * 60)

    if llm:
        print("Generating answer...")
        chain = (
            {"context": lambda x: format_docs(retrieved_docs), "question": lambda x: x}
            | prompt
            | llm
            | StrOutputParser()
        )
        try:
            response = chain.invoke(query)
            print("FINAL ANSWER:")
            print(response)
        except Exception as e:
            print(f"Error generating answer: {e}")
    else:
        print("(LLM generation skipped due to missing configuration)")
    print("="*60)

def main():
    if not os.path.exists(INDEX_DIR):
        print(f"Index directory '{INDEX_DIR}' not found. Please run ingest.py first.")
        return

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    try:
        vector_store = FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
    except Exception as e:
        print(f"Error loading FAISS index: {e}")
        return

    llm = get_llm()
    
    template = """Answer the question based only on the following context:
{context}

Question: {question}

Answer:"""
    prompt = ChatPromptTemplate.from_template(template)

    test_queries = [
        "What is Indecimal?",
        "What are the different construction packages available?",
        "What is the price per sqft for the Premier package?",
        "Which steel brands are used in the Pinnacle package?",
        "What is the wallet allowance for main doors in the Essential package?",
        "How does the escrow-based payment model work?",
        "What happens if there is a construction delay?",
        "How many quality checkpoints does Indecimal use?",
        "What is included in the Zero Cost Maintenance Program?",
        "Does Indecimal help with home financing?",
        "What is the floor-to-floor ceiling height?",
        "What brands of paint are used for the Infinia package?",
        "How are contractor payments released?",
        "What are the differentiators of Indecimal?",
        "Explain the partner onboarding process."
    ]

    print(f"Starting Quality Analysis on {len(test_queries)} queries...\n")
    for q in test_queries:
        run_test_query(q, vector_store, llm, prompt)

if __name__ == "__main__":
    main()
