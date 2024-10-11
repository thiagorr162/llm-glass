from pathlib import Path

# Caminhos das pastas
input_folder = Path("/home/thiagorr/Projects/llm-glass/data/patents")
output_folder = Path("data/processed")

# Certifique-se de que a pasta de saída existe
output_folder.mkdir(parents=True, exist_ok=True)


# Função para processar um único arquivo de tabelas
def process_file(filepath):
    with filepath.open("r") as file:
        content = file.read()

    # Quebra o conteúdo em seções de tabelas
    tables = content.split("\n\n")  # Separação por linha em branco

    # Variável para controlar o número da tabela
    table_number = filepath.stem.split("_")[1]
    table_count = 0

    # Processar cada tabela separadamente
    for table in tables:
        lines = table.strip().split("\n")

        # Verifica se tem mais de 10 linhas (para garantir que seja uma tabela válida)
        if len(lines) > 10:
            output_filepath = output_folder / f"table_{table_number}_{table_count}.csv"

            # Escreve diretamente no arquivo CSV
            with output_filepath.open("w") as csv_file:
                for line in lines:
                    csv_file.write(line + "\n")  # Escreve cada linha diretamente no arquivo CSV

            table_count += 1


# Processar todos os arquivos em subpastas da pasta de entrada
for txt_file in input_folder.rglob("table_*.txt"):
    process_file(txt_file)
