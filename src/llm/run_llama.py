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

    llm = ChatOllama(model="llama3.1", temperature=0.8, format="json")

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
output_directory = Path("data/llm_output")
output_directory.mkdir(parents=True, exist_ok=True)  # Cria o diretório se ele não existir

# Iterar por todos os arquivos JSON no diretório
for json_file in json_directory.glob("*.json"):
    output_file = output_directory / json_file.with_suffix(".txt").name

    # Verificar se o arquivo de saída já existe
    if not output_file.exists():
        with open(json_file, "r", encoding="utf-8") as f:
            # Ler o conteúdo do arquivo JSON
            data = json.load(f)

        # Rodar o LLM
        llm_output = run_llm(data)

        # Criar uma string que combina os dados originais e a saída do LLM
        combined_output = {"original_data": data, "llm_output": llm_output}

        # Escrever a combinação dos dados originais e a saída do LLM em um arquivo de texto
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(combined_output, f, ensure_ascii=False, indent=4)

        print(f"LLM output saved to {output_file}")

    else:
        print(f"LLM output already exists for {json_file}. Skipping...")
