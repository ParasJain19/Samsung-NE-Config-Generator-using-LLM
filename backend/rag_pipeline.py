import pandas as pd
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import DataFrameLoader
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

# ======== Prompt Templates ======== #
prompt_templates = {
    "summary": ChatPromptTemplate.from_template(
        """Summarize the following content in bullet points:\n<context>\n{context}\n</context>"""
    ),
    "explanation": ChatPromptTemplate.from_template(
        """Explain in detail using only the provided context:\n<context>\n{context}\n</context>\nQuestion: {input}"""
    ),
    "factual": ChatPromptTemplate.from_template(
        """Answer the following question based only on the provided context.\n<context>\n{context}\n</context>\nQuestion: {input}"""
    ),
    "json": ChatPromptTemplate.from_template(
        """Based only on the following context, generate a structured JSON answer for the given NE:\n<context>\n{context}\n</context>\nQuestion: {input}"""
    )
}


def build_pipeline(prompt_mode="factual"):
    # Load Excel & flatten multi-index columns
    df = pd.read_excel("network_elements_with_yearwise_versions.xlsx", sheet_name="Network Elements", header=[0, 1]).fillna("Unknown")
    df.columns = [f"{sec.strip()} - {param.strip()}" for sec, param in df.columns]

    # Convert rows to documents
    docs = []
    for _, row in df.iterrows():
        text = "\n".join([f"{col}: {row[col]}" for col in df.columns])
        docs.append({"content": text})
    df_docs = pd.DataFrame(docs)

    # Load & split documents
    loader = DataFrameLoader(df_docs, page_content_column="content")
    documents = loader.load()
    splitter = CharacterTextSplitter(chunk_size=1500, chunk_overlap=0)
    documents = splitter.split_documents(documents)

    # Setup retrievers
    bm25 = BM25Retriever.from_documents(documents, k=5)
    embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = Chroma.from_documents(documents, embedding=embedder, persist_directory="chroma_store")
    vect_retr = vectorstore.as_retriever(search_kwargs={"k": 5})
    hybrid = EnsembleRetriever(retrievers=[bm25, vect_retr], weights=[0.5, 0.5])

    # LLM (Gemini)
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key="API_KEy")

    # Select prompt
    selected_prompt = prompt_templates.get(prompt_mode, prompt_templates["factual"])

    # Updated LangChain 0.2+ Chains
    document_chain = create_stuff_documents_chain(llm=llm, prompt=selected_prompt)
    qa_chain = create_retrieval_chain(retriever=hybrid, combine_docs_chain=document_chain)

    return qa_chain


qa_chain_cache = {
    "factual": build_pipeline("factual")
}


def answer_question(query: str, mode="factual") -> str:
    try:
        if mode not in qa_chain_cache:
            qa_chain_cache[mode] = build_pipeline(mode)

        qa_chain = qa_chain_cache[mode]
        result = qa_chain.invoke({"input": query})
        if isinstance(result, dict):
            return result.get("answer") or result.get("result") or "No answer found."
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"
