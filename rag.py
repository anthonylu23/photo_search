from langchain_core.prompts import PromptTemplate
from vector_db import collection
from langsmith import traceable
from typing_extensions import List, TypedDict
from langchain_core.documents import Document
import os
from google import genai
from dotenv import load_dotenv
import base64
from llm import llm
from PIL import Image
from io import BytesIO

load_dotenv()

api_key = (
    os.getenv("GOOGLE_API_KEY")
    or os.getenv("GEMINI_API_KEY")
    or os.getenv("GOOGLE_GENAI_API_KEY")
)
if not api_key:
    raise RuntimeError(
        "Missing API key. Set 'GOOGLE_API_KEY' in your environment or .env file."
    )

client = genai.Client(api_key=api_key)
prompt = PromptTemplate.from_template(
    """You are a helpful assistant that answers questions about the user's photo library as best as possible. Include the image file name(s) in your response. 
    Be specific and concise about what you observe.
    Use dates, location, and other metadata when relevant.
    If you can't find the answer, say "I don't see that in your photos"
    Answer ONLY based on the provided base64 encoded images and metadata: {context}\n\n{question}"""
)

def image_encoding(image_file, max_size=(256, 256), quality=85):
    if image_file.mode in ("RGBA", "LA"):
        image = image_file.convert("RGB")
    else:
        image = image_file
    image.thumbnail((max_size), Image.Resampling.LANCZOS)
    buffer = BytesIO()
    image.save(buffer, format='JPEG', quality=quality, optimize=True)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return image_base64
    

@traceable
def search(question):
    result = collection.query(include=["embeddings", "metadatas"], query_texts=[question], n_results=3)
    metadatas = result.get("metadatas", [])
    context_dict = {}
    for metadata in metadatas:
        path = metadata[0]["file_path"]
        with Image.open(path) as image_file:
            image_base64 = image_encoding(image_file)
            context_dict[image_base64] = metadata
    return context_dict


@traceable
def explain(context, question):
    # prompt_text = prompt.format(context=context, question=question)
    # return llm.invoke(prompt_text)

    return client.models.generate_content(
        model="gemini-2.5-flash", contents=prompt.format(context=context, question=question)
    ).text

if __name__ == "__main__":
    question = "Which pictures were taken in Japan?"
    context = search(question)
    print(explain(context, question))