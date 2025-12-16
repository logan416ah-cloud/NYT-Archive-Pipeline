# This program pulls archived articles from the New York Times API.
# It requires a valid NYT API Key and a range of years to download.
#
# Note: The NYT API allows a maximum of 5 requests per minute, so
#       the program waits 12 seconds between requests.
#
# EXAMPLE USE FOR NYTArchiveClient:
#
# my_key = 'your NYT API key'
# client = NYTArchiveClient('my_key', 1996, 1999)
# client.start_download()
#
# This will download articles for every month between 1996 and 1999.
#
# IMPORTANT: You must have a valid NYT API Key for this to work.
#
# -------------------------------------------
# EXAMPLE USE FOR Tickler():
#
# tickle = Tickler()
# print(tickle.filter_by_headline('Trump'))
#
# EXAMPLE OUTPUT:
#
#         publish_date  section_name        headline              url
# 6         2023-11-14          U.S.    Blah Blah Blah...   https://www.nytimes.com/
# 29        2021-01-01       Climate    Blah Blah Blah...   https://www.nytimes.com/
# 79        2020-04-01      New York    Blah Blah Blah...   https://www.nytimes.com/
# 88        2017-09-04       Opinion    Blah Blah Blah...   https://www.nytimes.com/
# 91        2009-07-19          U.S.    Blah Blah Blah...   https://www.nytimes.com/
#
# [472 rows x 4 columns]


import requests
import pandas as pd
from datetime import datetime
from tqdm import tqdm
from pathlib import Path
import time
import re

# Rule sets for Presidents
PRESIDENT_RULES = {
    "William McKinley": {
        "include": {"william", "mckinley"},
        "exclude": set(),
    },
    "Theodore Roosevelt": {
        "include": {"theodore", "roosevelt"},
        "exclude": set(),
    },
    "William Howard Taft": {
        "include": {"william", "howard", "taft"},
        "exclude": set(),
    },
    "Woodrow Wilson": {
        "include": {"woodrow", "wilson"},
        "exclude": set(),
    },
    "Warren G. Harding": {
        "include": {"warren", "harding"},
        "exclude": set(),
    },
    "Calvin Coolidge": {
        "include": {"calvin", "coolidge"},
        "exclude": set(),
    },
    "Herbert Hoover": {
        "include": {"herbert", "hoover"},
        "exclude": set(),
    },
    "Franklin D. Roosevelt": {
        "include": {"franklin", "roosevelt"},
        "exclude": {"theodore"},
    },
    "Harry S. Truman": {
        "include": {"harry", "truman"},
        "exclude": set(),
    },
    "Dwight D. Eisenhower": {
        "include": {"dwight", "eisenhower"},
        "exclude": set(),
    },
    "John F. Kennedy": {
        "include": {"john", "kennedy"},
        "exclude": {"ted", "robert", "bob"},
    },
    "Lyndon B. Johnson": {
        "include": {"lyndon", "johnson"},
        "exclude": set(),
    },
    "Richard Nixon": {
        "include": {"richard", "nixon"},
        "exclude": set(),
    },
    "Gerald Ford": {
        "include": {"gerald", "ford"},
        "exclude": set(),
    },
    "Jimmy Carter": {
        "include": {"jimmy", "carter"},
        "exclude": set(),
    },
    "Ronald Reagan": {
        "include": {"ronald", "reagan"},
        "exclude": set(),
    },
    "George H. W. Bush": {
        "include": {"george", "bush"},
        "exclude": set(),
        "start": 1989,
        "end": 1993,
    },
    "George W. Bush": {
        "include": {"george", "bush"},
        "exclude": set(),
        "start": 2001,
        "end": 2009,
    },
    "Bill Clinton": {
        "include": {"bill", "clinton"},
        "exclude": {"hillary"},
    },
    "Barack Obama": {
        "include": {"barack", "obama"},
        "exclude": set(),
    },
    "Donald Trump": {
        "include": {"donald", "trump"},
        "exclude": set(),
    },
    "Joe Biden": {
        "include": {"joe", "biden"},
        "exclude": {"hunter"},
    },
}

BUSH_CONTEXT = {
    "president",
    "administration",
    "administrations",
    "iraq",
    "iraqi",
    "war",
    "afghanistan",
    "afghan",
    "election",
    "terrorism",
    "terrorists",
    "attacks",
    "policy",
    "policies",
}


class NYTArchiveClient:
    """
    A client for downloading New York Times articles from the archive API.

    Attributes:
        years (range): Range of years to download.
        months (range): Range of months (1-12) to download.
        api_key (str): NYT API key.
    """

    def __init__(self, api_key: str, year1: int, year2: int) -> None:
        """
        Initializes the client with a year range and validates the API key.

        Args:
            api_key(str): Your NYT API key.
            year1 (int): Starting year for archive download
            year2 (int): Ending year for archive download

        Raises:
            ValueError: If the API key is invalid, years are not integers.
                        year1 > year2, or years are not in range.
        """

        if not self.validate_key(api_key):
            raise ValueError("Invalid NYT API key")
        try:
            year1 = int(year1)
            year2 = int(year2)
        except ValueError:
            raise ValueError("year1 and year2 must be integers")

        if year1 > year2:
            raise ValueError("year1 must be less than or equal to year2")
        if not self.is_valid_year(year1) or not self.is_valid_year(year2):
            raise ValueError(
                "NYT archive starts at 1851"
                "Please enter a year range that starts after 1851"
            )

        self.years = range(year1, year2 + 1)
        self.months = range(1, 13)
        self.api_key = api_key
        self.params = {"api-key": api_key}

        self.create_all_files()

    def create_all_files(self) -> None:
        """
        Create the file architecture for saving data
        """
        base_path = Path(__file__).parent

        main_directory = base_path / "NYT_Data"
        main_directory.mkdir(exist_ok=True)

        query_folder = base_path / "Custom_Search_Folder"
        query_folder.mkdir(exist_ok=True)

        decades = [
            (1850, 1859),
            (1860, 1869),
            (1870, 1879),
            (1880, 1889),
            (1890, 1899),
            (1900, 1909),
            (1910, 1919),
            (1920, 1929),
            (1930, 1939),
            (1940, 1949),
            (1950, 1959),
            (1960, 1969),
            (1970, 1979),
            (1980, 1989),
            (1990, 1999),
            (2000, 2009),
            (2010, 2019),
            (2020, 2029),
        ]

        # For every decade create a folder
        for start, end in decades:
            decade_path = main_directory / f"{start}-{end}"
            decade_path.mkdir(exist_ok=True)

            # Create a folder for every year within that decade
            for year in range(start, end + 1):
                year_folder = decade_path / f"{year}_archive"
                year_folder.mkdir(exist_ok=True)

    @staticmethod
    def validate_key(api_key: str) -> bool:
        """
        Validates your API key by using a test request.

        Args:
            api_key (str): NYT API key to validate

        Returns:
            bool: True if key is valid, False if not.
        """

        test_url = "https://api.nytimes.com/svc/archive/v1/2024/1.json"
        try:
            response = requests.get(test_url, params={"api-key": api_key}, timeout=7)
            if response.status_code == 200:
                return True
            else:
                print(
                    f"WARNING: API KEY may be invalid. Status code: {response.status_code}"
                )
        except requests.RequestException as e:
            print(f"WARNING: API KEY check failed. Error: {e}")
        return False

    @staticmethod
    def is_valid_year(year: int) -> bool:
        """
        Validates whether if a year falls within the valid NYT archive range.

        Args:
            year (int):Year to check.

        Returns:
            bool: True if year is between 1851 and the current year. False if not.
        """
        try:
            year = int(year)
        except ValueError:
            return False
        return 1851 <= year <= datetime.today().year

    def start_download(self) -> None:
        """
        Downloads NYT articles for the specified year/month range
        and saves each month as a CSV file in 'NYT_Data' folder.
        """
        base_path = Path(__file__).parent
        folder = base_path / "NYT_Data"

        # Loop through the years and months, download data
        for year in tqdm(self.years, desc="Years"):
            for month in tqdm(self.months, desc=f"Year {year}", leave=False):
                baseurl = f"https://api.nytimes.com/svc/archive/v1/{year}/{month}.json"
                response = requests.get(baseurl, params=self.params)

                try:
                    data = response.json()
                except ValueError:
                    print(f"Error: Invalid JSON for: {year} and {month}")
                    continue

                docs = data.get("response", {}).get("docs", [])
                article_list = []

                # Extract relevant article information
                for article in docs:
                    pub_date = article.get("pub_date")
                    section_name = article.get("section_name")
                    headline = article.get("headline", {}).get("main")
                    web_url = article.get("web_url")

                    article_dict = {
                        "publish_date": pub_date,
                        "section_name": section_name,
                        "headline": headline,
                        "url": web_url,
                    }
                    article_list.append(article_dict)

                # Convert to DataFrame
                article_df = pd.DataFrame(article_list)

                if not article_df.empty:
                    # Standardize data format
                    article_df["publish_date"] = pd.to_datetime(
                        article_df["publish_date"]
                    ).dt.strftime("%Y-%m-%d")

                # Save CSV for each month
                decade_start = (year // 10) * 10
                decade_end = decade_start + 9

                decade_folder = folder / f"{decade_start}-{decade_end}"

                year_folder = decade_folder / f"{year}_archive"
                file_path = year_folder / f"nyt_{year}_{month}.csv"

                article_df.to_csv(file_path, index=False)

                time.sleep(12)  # IMPORTANT - NYT API allows for 5 requests a minute.


class Tickler:
    """
    Dataset manager and analysis engine for NYT archive data.

    This class provides high-level operations for:
    - Combining archived CSV files into a unified dataset
    - Caching combined results to avoid redundant disk reads
    - Filtering articles by date, section, or headline content
    - Normalizing text for consistent token-based analysis
    - Performing rule-based entity classification at scale

    The class is optimized for large datasets and supports
    efficient analysis across millions of articles.
    """

    def __init__(self) -> None:
        self.start_year = 1851
        self.end_year = datetime.today().year

        self._combined = None
        self._snapshot = {}

        base_path = Path(__file__).parent
        data_folder = base_path / "NYT_Data"
        if not data_folder.exists():
            print(
                "NYT_Data folder missing\n"
                "Creating folder now\n"
                "Be sure to run NYTArchiveClient.start_download() to download archives"
            )
            data_folder.mkdir()

    def combine_all(self, year1: int = None, year2: int = None) -> pd.DataFrame:
        """
        Combines all CSV files into a single DataFrame.

        Args:
            year1 (int, optional): Start year to filter files.
            year2 (int, optional): End year to filter files.

        Returns:
            pd.DataFrame: Combined DataFrame of all CSV articles.
        """

        # Base project directory
        base_path = Path(__file__).parent
        
        # Directory that contains all archived NYT CSV files.
        data_path = base_path / "NYT_Data"

        # If a year range is provided, combine only those years
        # Otherwise, combine all CSV files
        if year1 is not None and year2 is not None:
            search_path = data_path / f"{year1}-{year2}"
        else:
            search_path = data_path

        files = list(search_path.rglob("nyt_*.csv"))

        # Capture last-modified timestamps to support caching
        current_snapshot = {f: f.stat().st_mtime for f in files}

        # If dataset already combined, return cached DataFrame
        if self._combined is not None and current_snapshot == self._snapshot:
            return self._combined

        mainframe = []

        # Load CSV file files 
        for f in tqdm(files, desc="Loading NYT Archive CSVs", unit="file"):
            try:
                df = pd.read_csv(f)

            # IMPORTANT! Some NYT archive months have no data.
            # Skips over files with no data.
            except pd.errors.EmptyDataError:
                print(f"\nEmpty CSV skipped: {f}")
                continue

            if df.empty:
                print(f"No data within {f}")
                continue
            
            # Normalize headlines for token based analysis
            df["headline_norm"] = df["headline"].apply(self.normalize)
            df["publish_date"] = pd.to_datetime(df["publish_date"])

            mainframe.append(df)

        self._combined = (
            pd.concat(mainframe, ignore_index=True) if mainframe else pd.DataFrame()
        )
        self._snapshot = current_snapshot

        return self._combined

    def filter_by_date(self, year1: int, year2: int, save: bool = False) -> pd.DataFrame:
        """
        Filters the dataset by a year range.

        Args:
            year1 (int): Start year for filtering.
            year2 (int): End year for filtering.
            save (bool): Whether to save the filtered results to disk.

        Returns:
            pd.DataFrame: DataFrame containing articles published within the
            specified year range.
        """

        # Create a dataframe with the specified years
        df = self.combine_all(year1, year2)

        if df.empty:
            return pd.DataFrame()

        if save:
            base_path = Path(__file__).parent
            save_path = base_path / "Custom_Search_Folder"
            save_path.mkdir(exist_ok=True)

            file_path = save_path / f"filtered_{year1}-{year2}.csv"
            df.to_csv(file_path, index=False)

            print(f"Saved search results to {file_path}")

        return df

    def filter_by_section(self, section: str, save: bool = False) -> pd.DataFrame:
        """
        Filters the combined dataframe by section name (case-insensitive)

        Args:
            section (str)

        Returns:
            pd.DataFrame: Filtered DataFrame.
        """

        df = self.combine_all()

        # Return empty DataFrame so program doesn't crash
        if df.empty:
            return pd.DataFrame()

        # Articles that contain the specified section
        result = df[df["section_name"].str.contains(section, case=False, na=False)]

        # Clean and determine the file path to save
        if save:
            base_path = Path(__file__).parent
            save_path = base_path / "Custom_Search_Folder"
            save_path.mkdir(exist_ok=True)

            safe_section = section.lower().replace(" ", "_").replace("/", "-")

            file_path = save_path / f"filtered_section_{safe_section}.csv"
            result.to_csv(file_path, index=False)

            print(f"Saved search results to {file_path}")

        return result

    def filter_by_headline(
        self, filename: str, *keywords: str, save: bool = False, exact: bool = False
    ) -> pd.DataFrame:
        """
        Filter articles by normalized headline keywords.

        Args:
            filename (str): Base filename for saved results.
            *keywords (str): One or more keywords to match.
            save (bool): Whether to save results to disk.
            exact (bool): Whether to enforce exact-word boundaries.

        Returns:
            pd.DataFrame: Filtered subset of articles matching keywords.
        """
        df = self.combine_all()

        # Return an empty DataFrame so program doesn't crash
        if df.empty or not keywords:
            return pd.DataFrame()

        if exact:
            # Regex for exact matches
            filter_keywords = r"\b(?:%s)\b" % "|".join(keywords).lower()
        else:
            filter_keywords = "|".join(keywords).lower()


        result = df[df["headline_norm"].str.contains(filter_keywords)]

        if save:
            base_path = Path(__file__).parent
            save_path = base_path / "Custom_Search_Folder"
            save_path.mkdir(exist_ok=True)
            safe_fileame = filename.lower().replace(" ", "_")

            file_path = save_path / f"filtered_headline_{safe_fileame}.csv"
            result.to_csv(file_path, index=False)

            print(f"Saved search results to {file_path}")

        return result

    @staticmethod
    def normalize(text) -> str:
        """
        Normalize text for token-based comparison.

        This function converts text to lowercase, removes punctuation,
        collapses multiple spaces, and trims whitespace.

        Args:
            text (str): Input text to normalize.

        Returns:
            str: Normalized text for tokenization.
        """
        if not isinstance(text, str):
            return ""

        text = text.lower()

        # Exclude any character other than letters and numbers
        text = re.sub(r"[^a-z0-9\s]", " ", text)

        # Replace multiple spaces with only one
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def count_presidents(self, rules: dict) -> dict:
        """
        Count presidential mentions (from headlines) using rule-based classification.

        Iterates through normalized article headlines and counts mentions of each
        U.S. president using token-based namne matching.

        Args:
            rules (dict): Mapping of president names to matching rules.

        Returns:
            dict: Mapping of president names and mention counts.
        """
        df = self.combine_all()
        if df.empty:
            return {}

        counts = {name: 0 for name in rules}

        # Go through the articles in the dataset
        for row in tqdm(
            df.itertuples(index=False),
            total=len(df),
            desc="Classifying Presidents",
            unit="articles",
        ):
            headline = row.headline_norm
            publish_date = row.publish_date

            if not isinstance(headline, str):
                continue

            # Split headlines into tokens for matching
            tokens = set(headline.split())
            year = publish_date.year

            matched = False

            for name, rule in rules.items():
                if rule["include"].issubset(tokens) and rule["exclude"].isdisjoint(
                    tokens
                ):
                    counts[name] += 1
                    matched = True
                    break

            if matched:
                continue

            # Check to see if "bush" token and then intersect with the context
            if "bush" in tokens and tokens.intersection(BUSH_CONTEXT):
                for name, rule in rules.items():
                    if "start" in rule and "end" in rule:
                        if rule["start"] <= year <= rule["end"]:
                            counts[name] += 1
                            break

        return counts

    def show_available(self) -> pd.DataFrame:
        """
        Prints available months and sections in the combined dataset.
        """

        df = self.combine_all()
        if df.empty:
            return pd.DataFrame()

        df["publish_date"] = pd.to_datetime(df["publish_date"], errors="coerce")

        available_dates = df["publish_date"].dt.to_period("M").unique()
        available_sections = df["section_name"].dropna().unique()

        print("Available dates:")
        for d in sorted(available_dates):
            print(" -", d)

        print("Available sections:")
        for s in sorted(available_sections, key=str.lower):
            print(" -", s)


if __name__ == "__main__":
    api_key = input('Enter Your API Key: ') # Must add ***YOUR*** API key or program won't work

    year1 = input("Enter start year: ")
    year2 = input("Enter end year: ")

    client = NYTArchiveClient(api_key, year1, year2)
    client.start_download()

    # t = Tickler()
    # counts = t.count_presidents(PRESIDENT_RULES)

    # for name, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
    #     print(f"{name}: {count}")
