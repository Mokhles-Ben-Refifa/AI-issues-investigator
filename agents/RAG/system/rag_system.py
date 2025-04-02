# rag_serveur.py
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain.chains import RetrievalQA
from langchain.llms import HuggingFaceHub
import os

def initialize_rag_chain(document_path):
    """
    Charge un document .md ou .txt, construit l'index vectoriel et retourne un QA chain.
    """
    if not os.path.exists(document_path):
        raise FileNotFoundError(f"📂 Document introuvable : {document_path}")

    
    loader = TextLoader(document_path, encoding="utf-8")
    documents = loader.load()

    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    texts = text_splitter.split_documents(documents)


    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

  
    vectorstore = FAISS.from_documents(texts, embeddings)

  
    llm = HuggingFaceHub(repo_id="tiiuae/falcon-7b-instruct", model_kwargs={"temperature": 0.4, "max_new_tokens": 512})
    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=vectorstore.as_retriever())
    return qa_chain


def query_rag_chain(chain, root_cause):
    """Fait une requête au RAG avec le root cause comme question."""
    query = f"How to solve this system issue: {root_cause}?"
    response = chain.run(query)
    return response
