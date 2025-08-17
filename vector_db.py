import chromadb
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
from chromadb.utils.data_loaders import ImageLoader
from langchain_chroma import Chroma
from library import Library
import numpy as np

embedding_function = OpenCLIPEmbeddingFunction()
image_loader = ImageLoader()
chroma_client = chromadb.PersistentClient(path="./chroma_langchain_db")

def fetch_library(directory):
    library = Library(directory)
    ids = []
    metadatas = []
    images = []
    for data in library.data:
        ids.append(data["id"])
        md = data["metadata"].get_dict()
        md["filename"] = data["filename"]
        md["file_path"] = data["file_path"]
        md = {k: v for k, v in md.items() if v is not None}
        metadatas.append(md)
        images.append(data["image_np"])
    return ids, metadatas, images


def create_collection(collection_name):
    try:
        collection = chroma_client.get_collection(collection_name, 
                                                  embedding_function=embedding_function, 
                                                  data_loader=image_loader)
    except Exception:
        collection = chroma_client.create_collection(collection_name, 
                                                 embedding_function=embedding_function, 
                                                 data_loader=image_loader)
    return collection

def vectorize_directory(directory):
    ids, metadatas, images = fetch_library(directory)
    collection = create_collection("multimodal-collection")
    collection.add(ids=ids, 
                  metadatas=metadatas, 
                  images=images)
    vector_store = Chroma(collection_name="multimodal-collection", 
                      embedding_function=embedding_function,
                      persist_directory="./chroma_langchain_db")
    return vector_store, collection

vector_store, collection = vectorize_directory("../test_photos")