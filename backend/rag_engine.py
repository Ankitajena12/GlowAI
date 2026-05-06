from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import time

CHROMA_DIR   = r"C:\Users\ankit\OneDrive\Desktop\glowai\chroma_db"
EMBED_MODEL  = "all-MiniLM-L6-v2"
OLLAMA_MODEL = "gemma:2b"

PROMPT = PromptTemplate(
    template="""
You are GlowAI, a warm and knowledgeable skincare expert.
Use the information below to answer the question.
If the information does not cover it, say so honestly.
Always recommend a dermatologist for medical concerns.

Information:
{context}

Question: {question}

Answer helpfully and clearly:
""",
    input_variables=["context", "question"]
)


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


class GlowAIEngine:
    def __init__(self):
        self.vectorstore = None
        self.llm         = None
        self._ready      = False

    def load(self):
        try:
            print("Loading embeddings...")
            embeddings = HuggingFaceEmbeddings(
                model_name=EMBED_MODEL,
                model_kwargs={"device": "cpu"}
            )

            print("Loading ChromaDB...")
            self.vectorstore = Chroma(
                persist_directory=CHROMA_DIR,
                embedding_function=embeddings
            )

            print("Connecting to Ollama...")
            self.llm = OllamaLLM(model=OLLAMA_MODEL, temperature=0.7)

            self._ready = True
            print("GlowAI ready!")
            return True

        except Exception as e:
            print(f"Error loading engine: {e}")
            return False

    def ask(self, question: str) -> dict:
        if not self._ready:
            return {
                "answer": "Engine not ready. Please run build_db.py first.",
                "sources": [],
                "time_taken": 0
            }

        start = time.time()
        try:
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": 4})

            chain = (
                {"context": retriever | format_docs, "question": RunnablePassthrough()}
                | PROMPT
                | self.llm
                | StrOutputParser()
            )

            answer = chain.invoke(question)
            elapsed = round(time.time() - start, 1)

            # Get source docs separately for attribution
            docs = retriever.invoke(question)
            sources = list(set([
                doc.metadata.get("source", "").split("\\")[-1].split("/")[-1]
                for doc in docs
            ]))

            return {
                "answer": answer.strip(),
                "sources": sources,
                "time_taken": elapsed
            }

        except Exception as e:
            elapsed = round(time.time() - start, 1)
            err = str(e)
            if "connect" in err.lower():
                answer = "Cannot connect to Ollama. Make sure Ollama is running."
            else:
                answer = f"Something went wrong: {err}"
            return {"answer": answer, "sources": [], "time_taken": elapsed}


engine = GlowAIEngine()