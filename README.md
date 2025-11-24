# NYTimes Archive Scraper (NYTickler)

A Python-based toolset for downloading, caching, and analyzing historical New York Times article archives using the NYT Archive API.
This project was built to practice and demonstrate working with REST APIs, handling rate limits, data engineering (ETL), file system
automation, and large-scale data analysis with Pandas.

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
## Project Structure

The NYTickler project automatically builds and manages a clean directory layout for storing downloaded NYT archives and saved search results.
Below is the structure created when running the downloader and analysis tools:
```
NYT_Archive_Pipeline/
│── NYTickler.py
│── README.md
│── requirements.txt
│── .gitignore
│
│── NYT_Data/                # Created automatically when downloads begin
│   ├── 1990-1999/
│   │   ├── 1990_archive/
│   │   │   ├── nyt_1990_1.csv
│   │   │   ├── nyt_1990_2.csv
│   │   │   └── ...
│   │   ├── 1991_archive/
│   │   └── ...
│
│── Custom_Search_Folder/    # Created automatically when saving filtered results
│   ├── filtered_headline_war.csv
│   └── filtered_1996-04-16.csv

```
What these folders contain:
- NYT_Data/ — All downloaded NYT archive CSVs
- Decade folders (e.g., 1900-1909) — High-level organization by decade
- Year folders (e.g., 1905_archive) — Each month saved as one CSV
- Custom_Search_Folder/ — Saved outputs from your filter_by_*() functions

This structure ensures the dataset stays organized, scalable, and easy to work with for long-term analysis.
## API Key Setup

The script requires an NYT API Key from:  
https://developer.nytimes.com/

Insert your key: 
Be cognizant of hard coding your API Keys.

```python
api_key = "YOUR_NYT_API_KEY" 
```

---

## Usage Example

### Download NYT archives:

NYT limits requests to 5 per minute and 500 per day.
Larger date ranges may take significant time to download because each request must wait 12 seconds to respect NYT rate limits.

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
### Saving searches:

You can also save custom search queries by adding save=True.

```python
from NYTickler import Tickler

t = Tickler()
print(t.filter_by_date(1996, 4, 16, save=True))
```
This will save your search in a "Custom_Search_Folder" as "filtered_1996-04-16.csv"


