import multiprocessing
import re

from langchain_community.chat_models import ChatLlamaCpp
from langchain_core.prompts import ChatPromptTemplate


def split_document(document):
    return re.split(r"\n\s*\n", document)


file_path = "data/patente.txt"
grammar_path = "grammars/glasses.gbnf"

with open(file_path, "r") as file:
    data = file.read()

with open(grammar_path, "r") as file:
    grammar = file.read()

chunks = split_document(data)
chunk = chunks[17]

local_model = "models/Hermes-2-Pro-Llama-3-8B-Q8_0.gguf"


llm = ChatLlamaCpp(
    temperature=0.8,
    model_path=local_model,
    n_ctx=10000,
    # n_gpu_layers=8,
    # n_batch=10,  # Should be between 1 and n_ctx, consider the amount of VRAM in your GPU.
    max_tokens=5000,
    n_threads=multiprocessing.cpu_count() - 2,
    # repeat_penalty=1.5,
    # top_p=0.5,
    verbose=True,
    grammar=grammar,
)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant. Given the document related to glasses, "
            "your task is to analyze the document and extract the chemical composition of all glasses "
            "described in the document, detailing the percentage of each chemical element and the refractive index "
            "of each glass. If there is no relevant information, return 'there is no information'."
            "Here are the contents of the document:\n\n----\n\n{document}.",
        ),
        (
            "human",
            "{input}",
        ),
    ]
)
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant. Given the document related to glasses,"
            "your task is to analyze the document and extract the chemical composition of all glasses"
            "described in the document, detailing the percentage of each chemical element, and "
            "its refractive index."
            "Here are the contents of the document:\n\n----\n\n{document}.",
        ),
        (
            "human",
            "{input}",
        ),
    ]
)

chain = prompt | llm

ai_msg = chain.invoke(
    {
        "document": chunk,  # Passa o pedaço do documento
        "input": "List the chemical compositions of the glass mentioned in the document"
        "along with its refractive index. ",
    }
)


print(ai_msg.content)

breakpoint()
