import requests
import trafilatura

class ArticleScraper:

    def __init__(self, headers, timeout=30):

        self.headers = headers
        self.timeout = timeout

    def extract_article(self, url):

        try:

            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.timeout
            )

            if response.status_code != 200:

                return None

            downloaded = trafilatura.extract(
                response.text,
                include_comments=False,
                include_tables=False
            )

            return downloaded

        except Exception:

            return None