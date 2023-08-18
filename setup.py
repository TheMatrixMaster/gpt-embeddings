import os
import time
import pandas as pd
from zep_python import ZepClient
from zep_python.document import Document
from utils import *

zep_api_url = "http://localhost:8000"

client = ZepClient(base_url=zep_api_url)

"""
Step 1: Create a new collection in which to store our documents for a given task class
        We will use chatgpt embedding model which has embedding size of 768
"""

collection_name = "fever"

client.document.delete_collection(collection_name)

try:
    collection = client.document.add_collection(
        name=collection_name,  # required
        description="Fever Q&A embeddings",  # optional
        embedding_dimensions=1536,  # this must match the model you've configured for 
        is_auto_embedded=True,  # use Zep's built-in embedder. Defaults to True
    )
except Exception as e:
    print(e)


"""
Step 2: Chunk up documents into sections to be stored in the collection
        For now, we will use the custom splitting functions to handle the .txt files, but in the 
        future, I will require new docs to be sent in either csv, json, or yml format with clear
        question and answer fields
"""

DOC_DIR = "documents"
FILE_NAME = "documents/raw_convo.txt"

# Custom splitting for .txt file such that each entry in qa_data is a tuple of ([questions], answer)
# TODO: Add support for csv, json, and yml files
sections = split_into_sections(FILE_NAME)
qa_sections = split_into_qa_pairs(sections)
qa_data = []
for section, data in qa_sections:
    for questions, answer in data:
        qa_data.append((questions, answer))

# Split the qa pairs into chunks with a predefined max token length
MAX_TOKENS = 1600
qa_strings = []

for section in qa_data:
    qa_strings.extend(split_strings_from_subsection(section, max_tokens=MAX_TOKENS))


"""
Step 3: Embed the document chunks and store them into the collection
"""
documents = [
    Document(
        content=chunk,
        document_id=f"{collection_name}-{i}",  # optional document ID
        metadata={"bar": i},  # optional metadata
    )
    for i, chunk in enumerate(qa_strings)
]

uuids = collection.add_documents(documents)


"""
Step 4: Wait for the documents to be embedded and monitor the process
"""
while True:
    c = client.document.get_collection(collection_name)
    print(
        "Embedding status: "
        f"{c.document_embedded_count}/{c.document_count} documents embedded"
    )
    time.sleep(1)
    if c.status == "ready":
        break

print(f"Added {len(uuids)} documents to collection {collection_name}")
