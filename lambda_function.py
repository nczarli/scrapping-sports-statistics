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
import time
import tempfile


logging.basicConfig(level=print)


class SeleniumScraper:
    """Handles web scraping using Selenium."""

    def __init__(self, url):
        self.url = url
        self.driver = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def _initialize_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-dev-tools")
        chrome_options.add_argument("--no-zygote")
        chrome_options.add_argument("--single-process")
        chrome_options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")
        chrome_options.add_argument(f"--data-path={tempfile.mkdtemp()}")
        chrome_options.add_argument(f"--disk-cache-dir={tempfile.mkdtemp()}")
        chrome_options.add_argument("--remote-debugging-pipe")
        chrome_options.add_argument("--verbose")
        chrome_options.add_argument("--log-path=/tmp")
        chrome_options.binary_location = "/opt/chrome/chrome-linux64/chrome"
        chrome_options.add_argument(f"user-agent={self.headers['User-Agent']}")

        service = Service(
            executable_path="/opt/chrome-driver/chromedriver-linux64/chromedriver",
            service_log_path="/tmp/chromedriver.log"
        )

        self.driver = webdriver.Chrome(
            service=service,
            options=chrome_options
        )
 
        

    def fetch_html(self):
        """Fetches HTML content from the given URL."""
        self._initialize_driver()
        self.driver.get(self.url)

        time.sleep(5)

        self.driver.save_screenshot("screenshot.png")

        print(f"Waiting for page to load with table class")

    
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

        print(f"Uploaded file {filename} to S3 bucket {self.bucket_name}")


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
            print('Uploading CSV')
            # self.uploader.upload_csv(headers, rows)
            return {"statusCode": 200, "body": "Scraping completed successfully."}
        else:
            return {"statusCode": 500, "body": "Failed to extract data."}


def handler(event, context):
    print(f"Starting the NBA Team Stats Pipeline")
    pipeline = NBATeamStatsPipeline()
    return pipeline.run()
    