from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings


PERSIST_DIRECTORY = "./chroma_db"


def load_pdf(file_path):

    loader = PyPDFLoader(file_path)

    return loader.load()


def split_documents(documents):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " "
        ]
    )

    return splitter.split_documents(documents)


def get_embeddings():

    return OllamaEmbeddings(
        model="nomic-embed-text"
    )


def create_vector_store(documents):

    embeddings = get_embeddings()

    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )

    return vector_store


def get_retriever(vector_store):

    return vector_store.as_retriever(
        search_kwargs={
            "k": 8
        }
    )


def extract_text(documents):

    return "\n\n".join(
        document.page_content
        for document in documents
    )
