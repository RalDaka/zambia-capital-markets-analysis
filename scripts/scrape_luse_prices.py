import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os

url = "https://africanfinancials.com/lusaka-securities-exchange-share-prices/"

response = requests.get(url)
response.raise_for_status()

soup = BeautifulSoup(response.text, "lxml")

tables = pd.read_html(response.text)

print(f"Number of tables found: {len(tables)}")

for i, table in enumerate(tables):
    print(f"\nTable {i}")
    print(table.head())