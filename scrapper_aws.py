import os
import io
import csv
import logging
from datetime import datetime
import time
import boto3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class NBATeamStatsScraper:
    """
    A class to scrape NBA team statistics and upload to S3.
    """

    def __init__(self, url):
        self.url = url
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.logger = logging.getLogger(__name__)
        self.s3_bucket = os.getenv('S3_BUCKET_NAME')
        if not self.s3_bucket:
            raise ValueError("S3_BUCKET_NAME environment variable not set")
        self.s3_client = boto3.client('s3')

    def fetch_data(self):
        """
        Fetch HTML content using Selenium with headless Chrome.
        """
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920x1080")
            chrome_options.add_argument(f"user-agent={self.headers['User-Agent']}")

            # Configure for AWS Lambda if detected
            if os.environ.get('AWS_EXECUTION_ENV'):
                chrome_options.binary_location = "/opt/python/bin/headless-chromium"
                service = Service(executable_path="/opt/python/bin/chromedriver")
            else:
                service = Service(ChromeDriverManager().install())

            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.get(self.url)
            
            # Wait for the table to load
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "Crom_table__p1iZz"))
            )
            
            html = driver.page_source
            driver.quit()
            return html
        except Exception as e:
            self.logger.error(f"Failed to fetch data: {e}")
            return None

    def parse_data(self, html):
        """
        Parse HTML to extract team statistics.
        """
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", class_="Crom_table__p1iZz")
        if not table:
            self.logger.error("Table not found.")
            return None

        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        rows = table.find_all("tr")[1:]
        data = []
        for row in rows:
            cols = [col.get_text(strip=True) for col in row.find_all("td")]
            if cols:
                data.append(cols)
        return headers, data

    def generate_csv_data(self, headers, data):
        """
        Generate CSV content as a string.
        """
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(data)
        return output.getvalue()

    def upload_to_s3(self, csv_data, filename):
        """
        Upload CSV data to S3 bucket.
        """
        try:
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=filename,
                Body=csv_data.encode('utf-8'),
                ContentType='text/csv'
            )
            self.logger.info(f"Uploaded {filename} to S3 bucket {self.s3_bucket}")
        except Exception as e:
            self.logger.error(f"Failed to upload to S3: {e}")

    def run(self):
        """
        Execute scraping and upload to S3.
        """
        self.logger.info("Starting NBA team stats scraper...")
        html = self.fetch_data()
        if html:
            result = self.parse_data(html)
            if result:
                headers, data = result
                csv_data = self.generate_csv_data(headers, data)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"nba_team_stats_{timestamp}.csv"
                self.upload_to_s3(csv_data, filename)
        self.logger.info("Scraping completed.")

if __name__ == "__main__":
    url = "https://www.nba.com/stats/teams/traditional"
    scraper = NBATeamStatsScraper(url)
    scraper.run()