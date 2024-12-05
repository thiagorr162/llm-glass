# Google Patents Scraping

Here we describe how to run the scripts for collecting glass patent data from Google Patents.

## Downloading the Patents

To get started, execute the following command:

```
python src/scraping/get_patent_info.py -c {country} -w {wait} -p {n_pages} -k ["glass", "refractive"] --selenium_path {path_to_selenium_driver}
```

This script will download patents directly from Google Patents, filtering by the following parameters:

- **Country**: specified by the `{country}` argument
- **Wait time between requests**: adjustable with the `{wait}` parameter
- **Maximum number of pages**: set by `{n_pages}`
- **Keywords**: such as "glass" and "refractive," which can be adapted as needed
- **Directory for the Selenium driver**: here you need to specify where the Selenium WebDriver executable is located, defined by `{path_to_selenium_driver}`

## Processing the Patents

To process the patents, you must run the following scripts in this order:

```
src/data/read_html_tables.py
src/data/split_tables.py
src/data/process_tables.py
src/data/merge_tables.py
```
