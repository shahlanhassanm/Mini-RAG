import os
import glob
from typing import List

from langchain_community.document_loaders import PyPDFLoader, TextLoader

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Configuration
DATA_DIR = "data"
INDEX_DIR = "faiss_index"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

def load_documents(data_dir: str) -> List:
    documents = []
    # Look for both pdf and md files
    files = glob.glob(os.path.join(data_dir, "*.*"))
    
    if not files:
        print(f"No files found in {data_dir}.")
        return []

    print(f"Found {len(files)} files.")
    for file_path in files:
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in ['.pdf', '.md']:
            continue
            
        print(f"Loading {file_path}...")
        try:
            if ext == '.pdf':
                loader = PyPDFLoader(file_path)
            elif ext == '.md':
                loader = TextLoader(file_path, encoding='utf-8')
            
            docs = loader.load()
            documents.extend(docs)
            print(f"Loaded {len(docs)} document(s) from {file_path}")
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            
    return documents

def split_documents(documents: List) -> List:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")
    return chunks

def create_vector_store(chunks: List):
    print(f"Initializing embedding model: {EMBEDDING_MODEL_NAME}...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    
    print("Creating FAISS index...")
    vector_store = FAISS.from_documents(chunks, embeddings)
    
    print(f"Saving FAISS index to {INDEX_DIR}...")
    vector_store.save_local(INDEX_DIR)
    print("Vector store saved successfully.")

def main():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Created {DATA_DIR} directory. Please put your PDF files here.")
        return

    documents = load_documents(DATA_DIR)
    if not documents:
        return

    chunks = split_documents(documents)
    create_vector_store(chunks)

if __name__ == "__main__":
    main()
