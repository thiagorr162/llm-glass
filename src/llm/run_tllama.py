import json
from pathlib import Path

from bs4 import BeautifulSoup
from langchain.prompts import PromptTemplate
from langchain_ollama import ChatOllama


def run_llm(document):
    # Parse o HTML para extrair o texto da tabela
    soup = BeautifulSoup(document, "html.parser")
    table_text = soup.get_text()

    # Inicialize o modelo Ollama
    llm = ChatOllama(
        model="llama3.1",
        temperature=0.8,
        # format="json",
    )

    # Template de prompt para o modelo Ollama
    prompt_template = PromptTemplate(
        input_variables=["table_text"],
        template="""
        I will provide you with an HTML table. Your task is to extract all data as a csv. Do not return any extra text, only the csv table.

        Table content:
        {table_text}
        """,
    )
    # Formata o prompt com o conteúdo da tabela
    prompt = prompt_template.format(table_text=table_text)

    # Executa o modelo com o prompt
    response = llm.invoke(prompt)  # Usa invoke para processar o prompt diretamente

    print(response.content)
    breakpoint()
    return response.content  # Retorna o conteúdo gerado pelo modelo


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
                # Iterar por todas as tabelas no arquivo JSON e passar cada uma para o LLM
                for tab in data["tables"]:
                    llm_output = run_llm(tab)  # Passar o HTML da tabela diretamente para o LLM

                    # Adicionar a saída ao JSON
                    data.setdefault("llm_output", []).append(llm_output)

                # Salvar a saída em um novo arquivo de texto na pasta de output
                with open(output_file, "w", encoding="utf-8") as out_f:
                    out_f.write(json.dumps(data, indent=4))

                print(f"LLM output saved for {json_file.name}.")
    else:
        print(f"Output for {json_file.name} already exists.")
