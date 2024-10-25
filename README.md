# Google Patents Scraping

Aqui descrevemos como rodar os códigos para coleta de dados de patentes de vidros no Google Patents.

## Baixando as patents

Para iniciar, execute o seguinte comando:

```
python src/scraping/get_patent_info.py -c {country} -w {wait} -p {n_pages} -k ["glass", "refractive"]
```


Este script irá realizar o download de patentes diretamente do Google Patents, filtrando pelos seguintes parâmetros:

- **País**: especificado pelo argumento `{country}`
- **Tempo de espera entre requisições**: ajustável com o parâmetro `{wait}`
- **Número máximo de páginas**: configurado por `{n_pages}`
- **Palavras-chave**: como "glass" e "refractive", que podem ser adaptadas conforme necessário.

## Procesando as patentes

Para processar as patents, você deve rodar os seguintes códigos, nessa ordem:

```
src/data/read_html_tables.py
src/data/split_tables.py
src/data/process_tables.py
src/data/merge_tables.py
```
