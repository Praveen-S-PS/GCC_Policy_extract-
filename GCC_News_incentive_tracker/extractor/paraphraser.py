import hashlib
import json
import os
import time

import requests


class OllamaParaphraser:

    HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

    DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")

    CACHE_PATH = "output/.paraphrase_cache.json"

    MIN_LEN = 80

    REQUEST_TIMEOUT = 120

    PROMPT_TEMPLATE = (
        "You are paraphrasing a single clause from a government policy "
        "document for a business reference workbook.\n\n"
        "Rules:\n"
        "- Output a single short paragraph in clear English, 1 to 3 sentences.\n"
        "- Preserve all numbers, percentages, currency amounts, and time "
        "periods exactly as in the input.\n"
        "- Drop legal boilerplate, navigation labels, table headers, and "
        "section codes.\n"
        "- If the input is in Spanish, French, Portuguese, or another "
        "language, translate to English as part of the paraphrase.\n"
        "- If the input is already concise and clear, return it unchanged.\n"
        "- Output the paraphrase only, no preamble, no markdown, no quotes.\n\n"
        "Input:\n{text}\n\nParaphrase:"
    )

    def __init__(self, model=None, host=None):

        self.model = model or self.DEFAULT_MODEL
        self.host = host or self.HOST
        self._cache = self._load_cache()
        self._dirty = False
        self._available = None

    def is_available(self):

        if self._available is not None:
            return self._available

        try:

            r = requests.get(f"{self.host}/api/tags", timeout=3)

            if r.status_code != 200:
                self._available = False
                return False

            tags = r.json().get("models", [])

            names = {t.get("name", "") for t in tags}

            if self.model not in names:

                print(
                    f"⚠ Ollama is running but model '{self.model}' is not "
                    f"installed. Run: ollama pull {self.model}"
                )

                self._available = False
                return False

            self._available = True
            return True

        except (requests.RequestException, ValueError):

            self._available = False
            return False

    def paraphrase(self, text):

        if not text or len(text) < self.MIN_LEN:
            return text

        text = text.strip()

        key = self._cache_key(text)

        if key in self._cache:
            return self._cache[key]

        if not self.is_available():
            return text

        try:

            r = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": self.PROMPT_TEMPLATE.format(text=text),
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "num_predict": 350,
                    },
                },
                timeout=self.REQUEST_TIMEOUT,
            )

            r.raise_for_status()

            out = r.json().get("response", "").strip()

            if not out or len(out) < 20:

                return text

            self._cache[key] = out

            self._dirty = True

            return out

        except (requests.RequestException, ValueError):

            return text

    def paraphrase_many(self, items, label=""):

        if not items:
            return []

        if not self.is_available():
            return items

        out = []

        total = len(items)

        for i, item in enumerate(items, start=1):

            if label:
                print(f"  paraphrase {label} [{i}/{total}]", end="\r")

            out.append(self.paraphrase(item))

            # Flush cache every 25 items
            if i % 25 == 0:
                self._save_cache()

        if label:
            print()  # newline after progress

        self._save_cache()

        return out

    def _cache_key(self, text):

        h = hashlib.sha1()
        h.update(self.model.encode("utf-8"))
        h.update(b"\n")
        h.update(text.encode("utf-8"))

        return h.hexdigest()

    def _load_cache(self):

        if not os.path.exists(self.CACHE_PATH):
            return {}

        try:

            with open(self.CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)

        except (OSError, json.JSONDecodeError):

            return {}

    def _save_cache(self):

        if not self._dirty:
            return

        os.makedirs(os.path.dirname(self.CACHE_PATH), exist_ok=True)

        with open(self.CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(self._cache, f, ensure_ascii=False, indent=2)

        self._dirty = False
