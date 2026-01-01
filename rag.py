import os
import json
import hashlib
import asyncio
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from langsmith import traceable

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings,
)
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser

# ---------------- EVENT LOOP FIX ----------------
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# ---------------- ENV ----------------
load_dotenv()
os.environ["LANGCHAIN_PROJECT"] = "RAGFINALBOT"

PDF_PATH = "SYSTEM-FINAL.pdf"
INDEX_ROOT = Path(".indices")
INDEX_ROOT.mkdir(exist_ok=True)

EMBED_MODEL = "models/text-embedding-004"
LLM_MODEL = "gemini-2.5-flash"

# ---------------- HELPERS ----------------
@traceable
def load_pdf(path: str):
    return PyPDFLoader(path).load()

def split_documents(docs):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    return splitter.split_documents(docs)

def build_vectorstore(splits):
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBED_MODEL)
    return FAISS.from_documents(splits, embeddings)

# ---------------- INDEX ----------------
def index_key():
    h = hashlib.sha256()
    h.update(PDF_PATH.encode())
    return h.hexdigest()

def load_or_build_index():
    index_dir = INDEX_ROOT / index_key()

    embeddings = GoogleGenerativeAIEmbeddings(model=EMBED_MODEL)

    if index_dir.exists():
        return FAISS.load_local(
            str(index_dir),
            embeddings,
            allow_dangerous_deserialization=True,
        )

    docs = load_pdf(PDF_PATH)
    splits = split_documents(docs)
    vs = build_vectorstore(splits)

    index_dir.mkdir(parents=True, exist_ok=True)
    vs.save_local(str(index_dir))
    return vs

# ---------------- RAG ----------------
llm = ChatGoogleGenerativeAI(model=LLM_MODEL, temperature=0)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "Answer only from the given context."),
        ("human", "Question:\n{question}\n\nContext:\n{context}"),
    ]
)

def format_docs(docs: List):
    return "\n\n".join(d.page_content for d in docs)

def ask_pdf(question: str) -> str:
    vectorstore = load_or_build_index()

    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    chain = (
        RunnableParallel(
            {
                "context": retriever | RunnableLambda(format_docs),
                "question": RunnablePassthrough(),
            }
        )
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain.invoke(question)
