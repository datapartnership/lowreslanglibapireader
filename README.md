# DDPLRLL Dataset Reader

Python client for the **Low Resource Language Library API**.  
Queries Croissant JSON-LD metadata, downloads the referenced PDF files, and saves a local JSON-LD with rewritten file paths.

## Installation

```bash
# From the project root (editable / dev install)
pip install -e .
```

## Configuration

All settings can be provided via **CLI flags**, **environment variables** (prefixed `DDPLRLL_`), or a `.env` file.

| Env Variable | CLI Flag | Default | Description |
|---|---|---|---|
| `DDPLRLL_API_BASE_URL` | `--api-url` | `https://lrllapi.azurewebsites.net` | Base URL of the API |
| `DDPLRLL_API_KEY` | `--api-key` | _(empty)_ | `X-Api-Key` header value |
| `DDPLRLL_KEYWORD` | `--keyword` | — | Filter by keyword |
| `DDPLRLL_THEME` | `--theme` | — | Filter by theme |
| `DDPLRLL_AUTHOR` | `--author` | — | Filter by author |
| `DDPLRLL_YEAR` | `--year` | — | Filter by year |
| `DDPLRLL_LIMIT` | `--limit` | `30` | Max file entries (1–100) |
| `DDPLRLL_OUTPUT_DIR` | `--output` | `./output` | Output directory |
| `DDPLRLL_DOWNLOAD_FILES` | `--no-download` | `true` | Download PDFs |
| `DDPLRLL_MAX_CONCURRENT_DOWNLOADS` | `--concurrency` | `5` | Parallel downloads |

## CLI Usage

```bash
# Full pipeline: query + download + save JSON-LD
ddplrll-reader run \
  --api-url https://lrllapi.azurewebsites.net \
  --api-key MY_KEY \
  --keyword malaria \
  --year 2024 \
  --limit 10 \
  --output ./my-output

# Query only (no file downloads)
ddplrll-reader run --api-key MY_KEY --keyword health --no-download

# Health check
ddplrll-reader health --api-url https://lrllapi.azurewebsites.net
```

## Python API

```python
from ddplrll_reader import DdplrllDatasetClient, Settings

# Configure
settings = Settings(
    api_base_url="https://lrllapi.azurewebsites.net",
    api_key="MY_KEY",
    output_dir="./output",
)

client = DdplrllDatasetClient(settings)

# Full pipeline: query → download PDFs → save JSON-LD
jsonld_path = client.run(keyword="malaria", year="2024", limit=10)
print(f"Saved to {jsonld_path}")

# Query only (returns raw dict)
data = client.query(keyword="health", theme="Education")

# Query with Pydantic validation
response = client.query_validated(keyword="malaria")
for dataset in response.graph or []:
    print(dataset.sc_name)
    for f in dataset.distribution or []:
        print(f"  {f.sc_name} → {f.sc_content_url}")
```

## Output Structure

```
output/
├── dataset.jsonld          # Croissant JSON-LD with local file paths
└── files/
    ├── file-2022-465a93ae.pdf
    ├── file-2022-1cafc7a4.pdf
    └── ...
```

After downloading, each `scContentUrl` in `dataset.jsonld` is rewritten from the remote URL to the absolute local path, e.g.:

```
"scContentUrl": "https://lrllapi.azurewebsites.net/api/files/file-2022-465a93ae"
→
"scContentUrl": "/Users/you/output/files/file-2022-465a93ae.pdf"
```

## Using with mlcroissant

The saved `dataset.jsonld` is a valid [Croissant 1.0](https://mlcommons.org/croissant/) document.
Install the `mlcroissant` package to load it directly:

```bash
pip install mlcroissant
```

### Load and iterate records

```python
from mlcroissant import Dataset

ds = Dataset(jsonld=jsonld_path)
records = ds.records("default")

for record in records:
    print(record)
```

### Inspect metadata

```python
from mlcroissant import Dataset

ds = Dataset(jsonld="output/dataset.jsonld")

# Top-level metadata
print(ds.metadata.name)
print(ds.metadata.description)

# List all record sets
for record_set in ds.metadata.record_sets:
    print(record_set.name, "–", len(record_set.fields), "fields")
```

### End-to-end: ddplrll-reader → mlcroissant

```python
from ddplrll_reader import DdplrllDatasetClient, Settings
from mlcroissant import Dataset

# 1. Query and download
client = DdplrllDatasetClient(Settings(
    api_base_url="https://lrllapi.azurewebsites.net",
    api_key="MY_KEY",
))
jsonld_path = client.run(keyword="health", year="2023", limit=50)

# 2. Load with mlcroissant
ds = Dataset(jsonld=jsonld_path)
for record in ds.records("default"):
    print(record)
```

## Using with pandas

```python
import json
import pandas as pd

# Load the JSON-LD
with open("output/dataset.jsonld") as f:
    data = json.load(f)

# Flatten all file objects across every dataset/year into a DataFrame
rows = []
for dataset_node in data.get("graph", []):
    dataset_id = dataset_node.get("id")
    year = dataset_node.get("scTemporalCoverage")
    for file_obj in dataset_node.get("distribution", []):
        rows.append({
            "dataset_id": dataset_id,
            "year": year,
            "file_id": file_obj.get("id"),
            "name": file_obj.get("scName"),
            "author": file_obj.get("scAuthor"),
            "local_path": file_obj.get("scContentUrl"),
            "size_bytes": file_obj.get("scContentSize"),
            "word_count": file_obj.get("scWordCount"),
            "token_count": file_obj.get("ddpvTokenCount"),
            "keywords": file_obj.get("scKeywords"),
            "themes": file_obj.get("dcatTheme"),
        })

df = pd.DataFrame(rows)
print(df.head())
print(f"\nTotal files: {len(df)}")
print(f"Total tokens: {df['token_count'].sum():,}")
```

## Using with Hugging Face Datasets

```python
import json
from datasets import Dataset

with open("output/dataset.jsonld") as f:
    data = json.load(f)

# Build a flat list of records
records = []
for dataset_node in data.get("graph", []):
    for file_obj in dataset_node.get("distribution", []):
        records.append({
            "file_id": file_obj["id"],
            "name": file_obj.get("scName"),
            "author": file_obj.get("scAuthor"),
            "year": dataset_node.get("scTemporalCoverage"),
            "local_path": file_obj.get("scContentUrl"),
            "word_count": file_obj.get("scWordCount"),
            "token_count": file_obj.get("ddpvTokenCount"),
            "keywords": ", ".join(file_obj.get("scKeywords", [])),
            "themes": ", ".join(file_obj.get("dcatTheme", [])),
        })

ds = Dataset.from_list(records)
print(ds)
print(ds[0])

# Filter, shuffle, split
ds_health = ds.filter(lambda r: "Health" in r["themes"])
train_test = ds_health.train_test_split(test_size=0.2)
print(train_test)
```


## End-to-end: query → pandas → analysis

```python
from ddplrll_reader import DdplrllDatasetClient, Settings
import pandas as pd

# 1. Query and download
client = DdplrllDatasetClient(Settings(
    api_base_url="https://lrllapi.azurewebsites.net",
    api_key="MY_KEY",
))
jsonld_path = client.run(keyword="health", year="2023", limit=50)

# 2. Load into pandas
import json
with open(jsonld_path) as f:
    data = json.load(f)

rows = [
    {
        "name": fo.get("scName"),
        "author": fo.get("scAuthor"),
        "words": fo.get("scWordCount"),
        "tokens": fo.get("ddpvTokenCount"),
        "themes": fo.get("dcatTheme"),
        "path": fo.get("scContentUrl"),
    }
    for node in data.get("graph", [])
    for fo in node.get("distribution", [])
]
df = pd.DataFrame(rows)

# 3. Analyse
print(df.describe())
print(df.groupby("author")["tokens"].sum().sort_values(ascending=False))
```

## License

MIT
