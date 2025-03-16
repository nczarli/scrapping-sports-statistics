# Download the latest version of ChromeDriver from the official site
# https://developer.chrome.com/docs/chromedriver/downloads

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import csv
import logging
from datetime import datetime
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class NBATeamStatsScraper:
    """
    A class to scrape NBA team statistics from the specified URL.

    Attributes:
        url (str): The URL to scrape the NBA team stats from.
        headers (dict): Headers used in the HTTP request to mimic a browser.
        logger (logging.Logger): Logger for logging messages and errors.
    """

    def __init__(self, url):
        """
        Initialize the scraper with the target URL.

        Args:
            url (str): The URL to scrape the NBA team stats from.
        """
        self.url = url
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.logger = logging.getLogger(__name__)

    def fetch_data(self):
        """
        Fetch HTML content using Selenium to handle JavaScript rendering.

        This method opens a headless browser, fetches the rendered HTML page, and returns it.

        Returns:
            str: The HTML content of the page after JavaScript execution.

        Raises:
            Exception: If there's an error while fetching the page.
        """
        try:
            # Setup Chrome options for headless mode
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in headless mode
            chrome_options.add_argument("--disable-gpu")  # Disable GPU hardware acceleration
            chrome_options.add_argument("--window-size=1920x1080")  # Set window size

            # Set User-Agent to mimic a real browser
            chrome_options.add_argument(f"user-agent={self.headers['User-Agent']}")

            # Initialize Selenium WebDriver with the headless option
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            driver.get(self.url)
            time.sleep(5)  # Increase sleep time to ensure the page fully loads

            # Take a screenshot for debugging if needed
            driver.save_screenshot("screenshot.png")

            html = driver.page_source
            driver.quit()  # Close the browser
            return html
        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            return None

    def parse_data(self, html):
        """
        Parse the HTML content to extract team statistics.

        Args:
            html (str): The HTML content of the page to parse.

        Returns:
            tuple: A tuple containing:
                - headers (list): The table headers extracted from the HTML.
                - data (list): The table data extracted from the HTML.

        Raises:
            ValueError: If the table or headers are not found in the HTML.
        """
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", class_="Crom_table__p1iZz")  # Ensure the correct class name here
        if not table:
            self.logger.error("Table not found on the page.")
            return None

        # Extract headers
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        if not headers:
            self.logger.error("No headers found in the table.")
            return None

        # Extract rows
        rows = table.find_all("tr")[1:]  # Skip header row
        data = []
        for row in rows:
            cols = [col.get_text(strip=True) for col in row.find_all("td")]
            if cols:  # Skip empty rows
                data.append(cols)

        return headers, data

    def save_to_csv(self, headers, data, filename):
        """
        Save the extracted data to a CSV file.

        Args:
            headers (list): The list of headers to write to the CSV.
            data (list): The list of rows of data to write to the CSV.
            filename (str): The name of the CSV file to save the data.

        Raises:
            IOError: If there's an error while saving the data to the file.
        """
        try:
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)  # Write headers
                writer.writerows(data)  # Write data rows
            self.logger.info(f"Data saved to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save data to CSV: {e}")

    def run(self):
        """
        Execute the scraper workflow.

        This method coordinates the process of fetching the HTML content, 
        parsing the data, and saving the result to a CSV file.
        """
        self.logger.info("Starting NBA team stats scraper...")
        html = self.fetch_data()
        if html:
            result = self.parse_data(html)
            if result:
                headers, data = result
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"nba_team_stats_{timestamp}.csv"
                self.save_to_csv(headers, data, filename)
        self.logger.info("Scraping completed.")

# Example usage
if __name__ == "__main__":
    url = "https://www.nba.com/stats/teams/traditional"
    scraper = NBATeamStatsScraper(url)
    scraper.run()
