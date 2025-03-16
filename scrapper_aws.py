import os
import io
import csv
import logging
from datetime import datetime
import boto3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)


class SeleniumScraper:
    """Handles web scraping using Selenium."""

    def __init__(self, url):
        self.url = url
        self.driver = None

    def _initialize_driver(self):
        """Initialize Selenium WebDriver with headless Chrome."""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920x1080")
        options.binary_location = "/opt/python/bin/headless-chromium"
        service = Service("/opt/python/bin/chromedriver")

        self.driver = webdriver.Chrome(service=service, options=options)

    def fetch_html(self):
        """Fetches HTML content from the given URL."""
        self._initialize_driver()
        self.driver.get(self.url)

        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "Crom_table__p1iZz"))
        )

        html = self.driver.page_source
        self.driver.quit()
        return html


class DataParser:
    """Parses HTML content to extract structured data."""

    @staticmethod
    def parse(html):
        """Extracts table data using BeautifulSoup."""
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", class_="Crom_table__p1iZz")

        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        rows = [[td.get_text(strip=True) for td in row.find_all("td")] for row in table.find_all("tr")[1:]]

        return headers, rows


class S3Uploader:
    """Handles uploading files to S3."""

    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client("s3")

    def upload_csv(self, headers, rows):
        """Uploads extracted data as a CSV file to S3."""
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(headers)
        writer.writerows(rows)

        filename = f"nba_team_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.s3_client.put_object(Bucket=self.bucket_name, Key=filename, Body=csv_buffer.getvalue())

        logging.info(f"Uploaded file {filename} to S3 bucket {self.bucket_name}")


class NBATeamStatsPipeline:
    """Pipeline to coordinate scraping, parsing, and uploading."""

    def __init__(self):
        self.scraper = SeleniumScraper("https://www.nba.com/stats/teams/traditional")
        self.uploader = S3Uploader(os.getenv("S3_BUCKET_NAME"))

    def run(self):
        """Runs the full pipeline: fetch, parse, and upload data."""
        html = self.scraper.fetch_html()
        headers, rows = DataParser.parse(html)

        if headers and rows:
            self.uploader.upload_csv(headers, rows)
            return {"statusCode": 200, "body": "Scraping completed successfully."}
        else:
            return {"statusCode": 500, "body": "Failed to extract data."}


def lambda_handler(event, context):
    pipeline = NBATeamStatsPipeline()
    return pipeline.run()
