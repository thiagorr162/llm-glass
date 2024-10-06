import json
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama


def run_llm(data):
    # Define o prompt template
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a knowledgeable assistant. Given the following document related to glass compositions, "
                "your task is to extract the chemical composition of each glass mentioned, "
                "detailing the percentage of each element using their chemical symbols (e.g., Si for Silicon, O for Oxygen), "
                "and listing the key properties associated with each glass. "
                "Return the information in the following structured JSON format:\n\n"
                "{{\n"
                "  'glass1': {{\n"
                "    'name': 'Glass Name',\n"
                "    'composition': {{\n"
                "      'Element 1': 'percentage',\n"
                "      'Element 2': 'percentage',\n"
                "      ...\n"
                "    }},\n"
                "    'properties': [\n"
                "      'Property 1',\n"
                "      'Property 2'\n"
                "    ]\n"
                "  }},\n"
                "  'glass2': {{\n"
                "    'name': 'Glass Name',\n"
                "    'composition': {{\n"
                "      'Element 1': 'percentage',\n"
                "      'Element 2': 'percentage',\n"
                "      ...\n"
                "    }},\n"
                "    'properties': [\n"
                "      'Property 1',\n"
                "      'Property 2'\n"
                "    ]\n"
                "  }}\n"
                "}}\n\n"
                "If no relevant information is found for a glass, respond with 'there is no information'."
                "Here are the contents of the document:\n\n----\n\n{document}.",
            ),
            ("human", "{input}"),
        ]
    )

    # Ajustar o tamanho da janela de contexto
    llm = ChatOllama(model="llama3.1", temperature=0.8, format="json", context_window_size=4096)

    # Combine o prompt com a LLM
    chain = prompt | llm

    ai_msg = chain.invoke(
        {
            "document": data,  # Pass the document chunk
            "input": (
                "Respond in JSON format. For each glass mentioned in the document, list the glass name followed by "
                "its chemical composition, with each element and its percentage on separate lines, "
                "formatted as:\n\n"
                "{{\n"
                "  'glass1': {{\n"
                "    'name': 'Glass Name',\n"
                "    'composition': {{\n"
                "      'Element 1': 'percentage',\n"
                "      'Element 2': 'percentage',\n"
                "      ...\n"
                "    }},\n"
                "    'properties': [\n"
                "      'Property 1',\n"
                "      'Property 2'\n"
                "    ]\n"
                "  }},\n"
                "  'glass2': {{\n"
                "    'name': 'Glass Name',\n"
                "    'composition': {{\n"
                "      'Element 1': 'percentage',\n"
                "      'Element 2': 'percentage',\n"
                "      ...\n"
                "    }},\n"
                "    'properties': [\n"
                "      'Property 1',\n"
                "      'Property 2'\n"
                "    ]\n"
                "  }}\n"
                "}}\n\n"
                "If there is no information about a specific glass, return 'there is no information'."
            ),
        }
    )

    return ai_msg.content


# Directory paths
json_directory = Path("data/patents")
output_directory = Path("data/llm_output")
output_directory.mkdir(parents=True, exist_ok=True)

# Iterar por todos os arquivos JSON no diretório
for json_file in json_directory.glob("*.json"):
    output_file = output_directory / f"{json_file.stem}.txt"

    # Verificar se o arquivo de saída já existe
    if not output_file.exists():
        with open(json_file, "r", encoding="utf-8") as f:
            # Ler o conteúdo do arquivo JSON
            data = json.load(f)

            # Rodar o modelo LLM se a key "llm_output" não existir
            if "llm_output" not in data:
                # Chamar o LLM e obter a saída
                llm_output = run_llm(data)

                # Adicionar a saída ao JSON
                data["llm_output"] = llm_output

                # Salvar a saída em um novo arquivo de texto na pasta de output
                with open(output_file, "w", encoding="utf-8") as out_f:
                    out_f.write(json.dumps(data, indent=4))

                print(f"LLM output saved for {json_file.name}.")
    else:
        print(f"Output for {json_file.name} already exists.")
