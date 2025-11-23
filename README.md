# NYTimes Archive Scraper (NYTickler)

A Python-based toolset for downloading, caching, and analyzing historical New York Times article archives using the NYT Archive API.

---

## Features

### **NYTArchiveClient**
- Downloads full monthly NYT article archives from 1851–present  
- Handles **rate limits** (5 requests/minute) with timed delays  
- Saves data as organized CSVs inside a structured folder system  
- Extracts article metadata including:
  - Publish date  
  - Section name  
  - Headline  
  - URL  

---

## Tickler (Data Analysis Tool)

### Capabilities:
- **Combines local CSV archives** into a single Pandas DataFrame  
- Smart caching to avoid re-reading unchanged files  
- Automatically skips empty or corrupted CSVs  
- Filtering functions:
  - `filter_by_headline()` – keyword search  
  - `filter_by_section()` – case-insensitive section search  
  - `filter_by_date()` – pull articles from a specific day  
- `show_available()` — lists all available months/sections

---

## Requirements

- Python 3.10+
- Packages:
  - `requests`
  - `pandas`
  - `tqdm`

Install dependencies:

```bash
pip install requests pandas tqdm
```

---

## API Key Setup

The script requires an NYT API Key from:  
https://developer.nytimes.com/

Insert your key:

```python
api_key = "YOUR_NYT_API_KEY"
```

---

## Usage Example

### Download NYT archives:

NYT limits requests to 5 per minute and 500 per day.
Larger date ranges will take longer to download due to rate-limiting.

Use this first to download files. 

```python
from NYTickler import NYTArchiveClient

api_key = "YOUR_NYT_API_KEY"

client = NYTArchiveClient(api_key, 1990, 1995)
client.start_download()
```

### Analyze articles:

Must contain CSV files in order to filter.

```python
from NYTickler import Tickler

t = Tickler()
df = t.filter_by_headline("election", "war")
print(df)
```

