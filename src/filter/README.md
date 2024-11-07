# Projeto de Filtragem e Análise de Dados

Este repositório contém um conjunto de funções em Python para realizar a filtragem e análise de dados de compostos químicos e propriedades associadas. O código foi desenvolvido para processar três arquivos CSV, aplicar filtros personalizados e gerar um DataFrame final com informações relevantes.

## Requisitos

Antes de começar, você precisará ter o seguinte instalado:

- **Python 3.x**
- **Bibliotecas Python**:
  - `pandas`
  - `json`
  - `re`
  - `pathlib`

## Descrição das Funções

O código contém várias funções que aplicam filtros aos dados de compostos químicos e propriedades. Abaixo está uma descrição detalhada de cada uma delas:

### 1. `Filter_By_Compounds(dataframe)`

Filtra as colunas do DataFrame com base nos compostos definidos no arquivo `properties.json`. Apenas as colunas que correspondem aos compostos desejados são mantidas.

**Parâmetros:**
- `dataframe`: DataFrame contendo os dados a serem filtrados.

**Retorno:**
- Um DataFrame filtrado contendo apenas as colunas que correspondem aos compostos desejados, conforme definido no JSON.
- Um DataFrame de exclusão contendo as colunas que não correspondem aos compostos desejados.

### 2. `Filter_by_have_numbers(dataframe)`

Filtra as colunas do DataFrame que contêm números em seus nomes. Isso pode ser útil para identificar colunas que possuem dados quantitativos ou numéricos.

**Parâmetros:**
- `dataframe`: DataFrame contendo os dados a serem filtrados.

**Retorno:**
- Um DataFrame filtrado contendo apenas as colunas que têm números no nome.
- Um DataFrame de exclusão contendo as colunas que não têm números no nome.

### 3. `Filter_by_2to8(dataframe)`

Filtra as colunas do DataFrame com base no comprimento do nome da coluna. Este filtro mantém apenas as colunas cujo nome tenha entre 2 e 8 caracteres.

**Parâmetros:**
- `dataframe`: DataFrame contendo os dados a serem filtrados.

**Retorno:**
- Um DataFrame filtrado contendo apenas as colunas cujos nomes têm entre 2 e 8 caracteres.
- Um DataFrame de exclusão contendo as colunas cujos nomes não atendem a esse critério de comprimento.

### 4. `Pull_Apart_Compoundsdataframe_NotCompoundsdataframe(dataframe)`

Esta função aplica os filtros `Filter_by_have_numbers` e `Filter_by_2to8` sequencialmente para separar as colunas de compostos das outras colunas. Ela mantém as colunas que atendem ao critério de ter números no nome e ter entre 2 e 8 caracteres no nome.

**Parâmetros:**
- `dataframe`: DataFrame contendo os dados a serem filtrados.

**Retorno:**
- Um DataFrame de compostos, contendo as colunas que atendem ao critério de ter números no nome e comprimento de 2 a 8 caracteres.
- Um DataFrame de exclusão, contendo as colunas que não atendem a esses critérios.

### 5. `Filter_by_not_plus(dataframe)`

Filtra as colunas que não contêm o caractere `+` no nome. Esse filtro pode ser útil quando se deseja excluir colunas com um padrão específico no nome (neste caso, o caractere `+`).

**Parâmetros:**
- `dataframe`: DataFrame contendo os dados a serem filtrados.

**Retorno:**
- Um DataFrame filtrado contendo apenas as colunas que não contêm o caractere `+` no nome.
- Um DataFrame de exclusão contendo as colunas que possuem o caractere `+`.

### 6. `insert_zeros(dataframe)`

Substitui valores `—` (travessões) e valores `NaN` (não numéricos) por 0 no DataFrame. Isso ajuda a limpar o DataFrame, tornando os dados mais consistentes e prontos para análise.

**Parâmetros:**
- `dataframe`: DataFrame contendo os dados a serem limpos.

**Retorno:**
- Um DataFrame limpo, onde os valores `—` e `NaN` foram substituídos por 0.

### 7. `remove_empty_columns(dataframe)`

Remove as colunas do DataFrame que contêm apenas valores 0. Colunas vazias podem ser removidas para melhorar a performance da análise e tornar o DataFrame mais enxuto.

**Parâmetros:**
- `dataframe`: DataFrame contendo os dados a serem filtrados.

**Retorno:**
- Um DataFrame filtrado sem as colunas vazias (que possuem apenas valores 0).
- Um DataFrame de exclusão contendo as colunas que foram removidas por estarem vazias.

### 8. `sum_lines(dataframe, tolerance=2)`

Filtra as linhas do DataFrame em que o somatório dos valores das colunas é próximo de 100, com uma tolerância definida (padrão de 2). Esse filtro pode ser útil para ajustar os dados e garantir que os valores somem a um valor esperado (por exemplo, em composição de materiais).

**Parâmetros:**
- `dataframe`: DataFrame contendo os dados a serem filtrados.
- `tolerance` (opcional): Valor que define a margem de erro para a soma, o padrão é 2.

**Retorno:**
- Um DataFrame filtrado contendo apenas as linhas cujo somatório das colunas é dentro do intervalo de 100 ± tolerância.
- Um DataFrame de exclusão contendo as linhas cujo somatório não está dentro do intervalo especificado.

### 9. `filter_by_properties(dataframe)`

Filtra as colunas do DataFrame que contêm propriedades químicas ou físicas específicas, como "refrativa", "densidade", "abbe", etc. Essas propriedades são definidas em uma lista fixa e são procuradas nos nomes das colunas.

**Parâmetros:**
- `dataframe`: DataFrame contendo os dados a serem filtrados.

**Retorno:**
- Um DataFrame filtrado contendo apenas as colunas que possuem as propriedades especificadas na lista.
- Um DataFrame de exclusão contendo as colunas que não possuem as propriedades desejadas.

### 10. `remove_rows_with_na(dataframe)`

Esta função remove linhas que contenham pelo menos um valor NaN (deve ser aplicada ao final do processo de filtragem)

**Parâmetros:**
- `dataframe`: DataFrame contendo os dados a serem filtrados.

**Retorno:**
- Um DataFrame filtrado contendo apenas as linhas que somam aproximadamente 100 e as colunas que contêm as propriedades desejadas.
- Um DataFrame de exclusão contendo as linhas que não atendem ao critério de soma e as colunas que não possuem as propriedades desejadas.

### 11. `all_filters(dataframe)`

Esta é a função principal que aplica todos os filtros definidos nas funções anteriores em sequência. Ela normaliza os dados, aplica filtros de compostos, propriedades, soma das linhas e remove colunas vazias, mantendo apenas dados relevantes para análise final.

**Parâmetros:**
- `dataframe`: DataFrame contendo os dados a serem filtrados.

**Retorno:**
- final_df: DataFrame filtrado final, contendo apenas as colunas e linhas que atendem a todos os critérios (compostos, propriedades desejadas e somatório das linhas próximo de 100).
- excluded_empty_columns: DataFrame com as colunas removidas por serem inteiramente vazias.
- excluded_sumlines: DataFrame com as linhas removidas devido ao somatório fora da faixa (98 a 102).
- excluded_plus_columns: DataFrame com as colunas removidas que contêm o caractere '+' no nome.
- excluded_rows_with_na: DataFrame com as linhas removidas devido a valores NaN
