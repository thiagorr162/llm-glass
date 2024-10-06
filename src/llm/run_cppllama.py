import json
import multiprocessing
from pathlib import Path

from langchain_community.chat_models import ChatLlamaCpp
from langchain_core.prompts import ChatPromptTemplate

grammar_path = "grammars/glasses.gbnf"

with open(grammar_path, "r") as file:
    grammar = file.read()

json_directory = Path("data/patents")
# Iterar por todos os arquivos JSON no diretório
for json_file in json_directory.glob("*.json"):
    with open(json_file, "r", encoding="utf-8") as f:
        # Ler o conteúdo do arquivo JSON
        data = json.load(f)
        data = data["claims"]
        # Adicionar o conteúdo à lista

        break

local_model = "models/Hermes-2-Pro-Llama-3-8B-Q8_0.gguf"

llm = ChatLlamaCpp(
    temperature=0.8,
    model_path=local_model,
    n_ctx=10000,
    # n_gpu_layers=8,
    # n_batch=10,  # Should be between 1 and n_ctx, consider the amount of VRAM in your GPU.
    # max_tokens=10000,
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
            "You are a knowledgeable assistant. Your task is to analyze the provided document "
            "related to glass compositions. Extract the chemical composition of each glass described, "
            "including the percentage of each chemical element and any relevant properties, and organize "
            "the information in a structured JSON format. "
            "Below is the document content:\n\n----\n\n{document}.",
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
        "document": data,  # passa o pedaço do documento
        "input": (
            "List the chemical compositions of the glass mentioned in the document, "
            "along with any relevant properties."
        ),
    }
)
print(ai_msg.content)

breakpoint()
