import json
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama


def run_llm(data):
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a knowledgeable assistant. Given the following document related to glass,"
                "your task is to analyze the document and extract the chemical composition of each glass mentioned,"
                "detailing the percentage of each element, using their chemical symbols "
                "(e.g., Si for Silicon, O for Oxygen), and listing the key properties associated with each glass."
                "Return the information in a structured format. If there is no relevant information, respond with"
                "'there is no information'. Here are the contents of the document:\n\n----\n\n{document}.",
            ),
            ("human", "{input}"),
        ]
    )

    llm = ChatOllama(
        model="llama3.1",
        temperature=0.8,
        format="json",
    )

    chain = prompt | llm

    ai_msg = chain.invoke(
        {
            "document": data,  # Pass the document chunk
            "input": (
                "Respond in JSON format. For each glass mentioned in the document, "
                "list the glass name followed by its chemical composition using the element symbols"
                " (e.g., Si for Silicon), and associated key properties. "
                "If there is no information about a specific glass, return 'there is no information'."
            ),
        }
    )

    return ai_msg  # Return the LLM output


json_directory = Path("data/patents")

# Iterar por todos os arquivos JSON no diretório
for json_file in json_directory.glob("*.json"):
    with open(json_file, "r", encoding="utf-8") as f:
        # Ler o conteúdo do arquivo JSON
        data = json.load(f)

    # Verificar se a chave "llm_output" já existe
    if "llm_output" not in data:
        # Se a chave não existir, rodar o LLM
        llm_output = run_llm(data)

        # Atribuir a saída do LLM à nova chave "llm_output"
        data["llm_output"] = llm_output

        # Salvar o arquivo JSON atualizado
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    else:
        print(f"LLM already processed for {json_file}. Skipping...")
