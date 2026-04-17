# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "beautifulsoup4",
# ]
# ///

import requests
from bs4 import BeautifulSoup

def scrape_ship_log(url):
    # Set a user-agent to mimic a browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        # Fetch the webpage
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise error for bad status codes

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the specific div containing the log text
        # This matches the <div class="work-page_text ltr"> element
        log_container = soup.find('div', class_='work-page_text')

        if log_container:
            # Extract text and handle line breaks/paragraphs
            # .get_text(separator="\n") preserves the structure better than simple .text
            extracted_text = log_container.get_text(separator="\n").strip()
            return extracted_text
        else:
            return "Could not find the log text container on this page."

    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"

base_url = "https://fromthepage.com/nharl/ships-logs-collection/ms220-log4"
output_file = "logsample.md"

with open(output_file, "a", encoding="utf-8") as f:
    for page in range(2, 11):
        url = f"{base_url}?page={page}"
        print(f"Scraping page {page}...")
        log_content = scrape_ship_log(url)
        f.write(f"## Page {page}\n\n")
        f.write(f"```\n{log_content}\n```\n\n")

print(f"Done. Results appended to {output_file}")