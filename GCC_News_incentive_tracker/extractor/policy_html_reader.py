import re

import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class PolicyHTMLReader:

    USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    TIMEOUT = 45

    DROP_TAGS = ("script", "style", "noscript", "nav", "header",
                 "footer", "aside", "form", "iframe")

    MIN_PARA_CHARS = 60

    WHITESPACE_RE = re.compile(r"\s+")

    @classmethod
    def read(cls, url):

        html = cls._fetch(url)

        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")

        for tag in soup(cls.DROP_TAGS):
            tag.decompose()

        paragraphs = []

        for el in soup.find_all(["p", "li", "td", "h2", "h3", "h4"]):

            text = el.get_text(separator=" ", strip=True)

            text = cls.WHITESPACE_RE.sub(" ", text).strip()

            if len(text) < cls.MIN_PARA_CHARS:
                continue

            paragraphs.append({
                "heading": "",
                "text": text,
            })

        return cls._dedupe(paragraphs)

    @classmethod
    def _fetch(cls, url):

        headers = {
            "User-Agent": cls.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,*/*",
        }

        for verify in (True, False):

            try:

                resp = requests.get(
                    url, headers=headers,
                    timeout=cls.TIMEOUT,
                    allow_redirects=True,
                    verify=verify,
                )

                if resp.status_code >= 400:
                    return None

                ctype = resp.headers.get("Content-Type", "")

                if "html" not in ctype.lower() and "text" not in ctype.lower():
                    return None

                return resp.text

            except requests.exceptions.SSLError:
                if verify:
                    continue
                return None

            except requests.RequestException:
                return None

        return None

    @staticmethod
    def _dedupe(paragraphs):

        seen = set()
        out = []

        for p in paragraphs:

            key = p["text"][:80]

            if key in seen:
                continue

            seen.add(key)
            out.append(p)

        return out
