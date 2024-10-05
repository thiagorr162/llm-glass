import re

import pytesseract
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pdf2image import convert_from_path

if False:
    pdf_path = "data/patente.pdf"
    pages = convert_from_path(pdf_path)

    full_text = ""

    for page_number, page in enumerate(pages):
        text = pytesseract.image_to_string(page)
        full_text += text

    with open("data/patente.txt", "w") as file:
        file.write(full_text)


def split_document(document):
    return re.split(r"\n\s*\n", document)


file_path = "data/patente.txt"

with open(file_path, "r") as file:
    data = file.read()


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a knowledgeable assistant. Given the following document related to glass,"
            "your task is to analyze the document and extract the chemical composition the given glass,"
            "detailing the percentage of each element, and "
            "listing the key properties associated with the glass."
            "If there is no relevant information, do not return a generic aswer, just say 'there is no information'."
            "Here are the contents of the document:\n\n----\n\n{document}.",
        ),
        ("human", "{input}"),
    ]
)

llm = ChatOllama(
    model="llama3.1",
    temperature=0.8,
)

chain = prompt | llm


chunks = split_document(data)

chunk = chunks[17:50]

ai_msg = chain.invoke(
    {
        "document": chunk,  # Passa o pedaço do documento
        "input": "Respond to me in JSON format. List the chemical compositions of the glass mentioned in the document"
        " along with the percentage of each element, and the key properties associated with each glass type. ",
    }
)

print(ai_msg)
