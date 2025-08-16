import chromadb
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
from chromadb.utils.data_loaders import ImageLoader
from langchain_chroma import Chroma
from library import Library

library = Library("/Users/anthony/Documents/CS/Coding/photo_query/test_photos")
ids = []
metadatas = []
uris = []
for data in library.data:
    ids.append(data["id"])
    md = data["metadata"].get_dict()
    md["filename"] = data["filename"]
    md = {k: v for k, v in md.items() if v is not None}
    metadatas.append(md)
    uris.append(data["file_path"])

embedding_function = OpenCLIPEmbeddingFunction()
image_loader = ImageLoader()

chroma_client = chromadb.PersistentClient(path="./chroma_langchain_db")

try:
    collection = chroma_client.get_collection("multimodal-collection", 
                                              embedding_function=embedding_function, 
                                              data_loader=image_loader)
except Exception:
    collection = chroma_client.create_collection("multimodal-collection", 
                                                 embedding_function=embedding_function, 
                                                 data_loader=image_loader)

collection.add(ids=ids, 
              metadatas=metadatas, 
              uris=uris)

vector_store = Chroma(collection_name="multimodal-collection", 
                      embedding_function=embedding_function,
                      persist_directory="./chroma_langchain_db")
