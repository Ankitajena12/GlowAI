from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

DOCS_DIR   = r"C:\Users\ankit\OneDrive\Desktop\glowai\skincare_docs"
CHROMA_DIR = r"C:\Users\ankit\OneDrive\Desktop\glowai\chroma_db"

def build():
    print("Loading documents...")
    loader = DirectoryLoader(DOCS_DIR, glob="*.txt", loader_cls=TextLoader)
    documents = loader.load()
    print(f"Loaded {len(documents)} files")

    print("Splitting into chunks...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=80)
    chunks = splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks")

    print("Loading embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print("Saving to ChromaDB...")
    Chroma.from_documents(chunks, embeddings, persist_directory=CHROMA_DIR)
    print("Done! Database ready.")

if __name__ == "__main__":
    build()