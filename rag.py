import os
import sys
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
# Try imports depending on what's available
try:
    from langchain_ollama import ChatOllama
except ImportError:
    from langchain_community.chat_models import ChatOllama

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Load env variables
load_dotenv()

INDEX_DIR = "faiss_index"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

def get_llm():
    # Helper to check if we should use Ollama or OpenRouter
    llm_type = os.getenv("LLM_TYPE", "openrouter").lower()
    
    if llm_type == "ollama":
        model_name = os.getenv("OLLAMA_MODEL", "llama3.2")
        print(f"Using Local Ollama model: {model_name}")
        # Base URL might be needed if not default
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return ChatOllama(model=model_name, base_url=base_url)
    
    elif llm_type == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("Error: OPENROUTER_API_KEY not found in environment variables.")
            print("Please create a .env file with OPENROUTER_API_KEY=your_key")
            sys.exit(1)
            
        model_name = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3-8b-instruct:free")
        print(f"Using OpenRouter model: {model_name}")
        return ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            model=model_name
        )
    else:
        print(f"Unknown LLM_TYPE: {llm_type}")
        print("Please set LLM_TYPE to 'ollama' or 'openrouter' in .env")
        sys.exit(1)

def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])

def main():
    if not os.path.exists(INDEX_DIR):
        print(f"Index directory '{INDEX_DIR}' not found. Please run ingest.py first.")
        return

    print("Loading vector store (this might take a moment)...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    try:
        vector_store = FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
    except Exception as e:
        print(f"Error loading FAISS index: {e}")
        return

    retriever = vector_store.as_retriever(search_kwargs={"k": 3})

    llm = get_llm()

    template = """Answer the question based only on the following context:
{context}

Question: {question}

Answer:"""
    prompt = ChatPromptTemplate.from_template(template)

    print("\n" + "="*50)
    print("Mini RAG Assistant initialized. Type 'exit' to quit.")
    print("="*50 + "\n")

    while True:
        try:
            query = input("Enter your query: ")
            if query.lower() in ['exit', 'quit', 'q']:
                break
            
            if not query.strip():
                continue

            print("\nRetrieving context...")
            retrieved_docs = retriever.invoke(query)
            
            # Display retrieved context (Transparency)
            print("\n" + "-"*20 + " RETRIEVED CONTEXT " + "-"*20)
            if not retrieved_docs:
                print("No relevant documents found.")
            
            for i, doc in enumerate(retrieved_docs):
                source = doc.metadata.get('source', 'Unknown')
                # Try to just show filename
                source = os.path.basename(source)
                print(f"Chunk {i+1} (Source: {source}):")
                content_preview = doc.page_content.replace('\n', ' ')
                print(content_preview[:300] + "..." if len(content_preview) > 300 else content_preview)
                print("-" * 10)
            print("-" * 59)

            print("\nGenerating answer...")
            chain = (
                {"context": lambda x: format_docs(retrieved_docs), "question": lambda x: x}
                | prompt
                | llm
                | StrOutputParser()
            )
            
            response = chain.invoke(query)
            print("\n" + "="*20 + " FINAL ANSWER " + "="*20)
            print(response)
            print("="*54 + "\n")
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error generating response: {e}")

if __name__ == "__main__":
    main()
