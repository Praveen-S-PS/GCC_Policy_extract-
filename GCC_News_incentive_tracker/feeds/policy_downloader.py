import json
import os
import ssl

import requests
import urllib3
from urllib3.util.ssl_ import create_urllib3_context

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class _LegacySSLAdapter(requests.adapters.HTTPAdapter):

    def init_poolmanager(self, *args, **kwargs):

        ctx = create_urllib3_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT

        kwargs["ssl_context"] = ctx

        return super().init_poolmanager(*args, **kwargs)


class PolicyDownloader:

    USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    TIMEOUT = 60

    PDF_MAGIC = b"%PDF"

    CACHE_FILENAME = ".cache.json"

    @classmethod
    def ensure(cls, url, dest_path, referer=None, force=False):

        cache_dir = os.path.dirname(dest_path)

        cache_path = os.path.join(cache_dir, cls.CACHE_FILENAME)

        cache = cls._load_cache(cache_path)

        cache_key = os.path.basename(dest_path)

        local_meta = cache.get(cache_key, {})

        if not force and cls._is_valid_pdf(dest_path):

            remote_meta = cls._head(url, referer=referer)

            if remote_meta is None:

                print(
                    f"  ✓ cached: {cache_key} "
                    f"(could not reach server to check freshness)"
                )
                return True

            if cls._is_fresh(local_meta, remote_meta):

                print(f"  ✓ cached, unchanged: {cache_key}")
                return True

            print(f"  ↻ remote PDF changed, refreshing {cache_key}")

        elif force:

            print(f"  ⟳ force refresh: {cache_key}")

        else:

            print(f"  ↓ downloading {cache_key} from {url}")

        result = cls._download(url, dest_path, referer=referer)

        if not result:
            return False

        cache[cache_key] = {
            "url": url,
            "etag": result.get("etag"),
            "last_modified": result.get("last_modified"),
            "content_length": result.get("content_length"),
        }

        cls._save_cache(cache_path, cache)

        return True

    @classmethod
    def _head(cls, url, referer=None):

        headers = {"User-Agent": cls.USER_AGENT}

        if referer:
            headers["Referer"] = referer

        for verify in (True, False):

            try:

                resp = requests.head(
                    url,
                    headers=headers,
                    timeout=cls.TIMEOUT,
                    allow_redirects=True,
                    verify=verify,
                )

                if resp.status_code >= 400:
                    return None

                return {
                    "etag": resp.headers.get("ETag"),
                    "last_modified": resp.headers.get("Last-Modified"),
                    "content_length": resp.headers.get("Content-Length"),
                }

            except requests.exceptions.SSLError:

                if verify:
                    continue
                return None

            except requests.RequestException:

                return None

    @classmethod
    def _is_fresh(cls, local, remote):

        for key in ("etag", "last_modified", "content_length"):

            l = local.get(key)
            r = remote.get(key)

            if l and r and l != r:
                return False

        return True

    @classmethod
    def _download(cls, url, dest_path, referer=None):

        headers = {
            "User-Agent": cls.USER_AGENT,
            "Accept": "application/pdf,*/*",
        }

        if referer:
            headers["Referer"] = referer

        captured = {}

        attempts = [
            ("standard", True, False),
            ("no-verify", False, False),
            ("legacy-ssl", False, True),
        ]

        success = False

        for label, verify, legacy in attempts:

            session = requests.Session()

            if legacy:
                session.mount("https://", _LegacySSLAdapter())

            try:

                response = session.get(
                    url,
                    headers=headers,
                    timeout=cls.TIMEOUT,
                    allow_redirects=True,
                    stream=True,
                    verify=verify,
                )

                response.raise_for_status()

                captured = {
                    "etag": response.headers.get("ETag"),
                    "last_modified": response.headers.get("Last-Modified"),
                    "content_length": response.headers.get("Content-Length"),
                }

                os.makedirs(os.path.dirname(dest_path), exist_ok=True)

                with open(dest_path, "wb") as f:

                    for chunk in response.iter_content(chunk_size=64 * 1024):

                        if chunk:
                            f.write(chunk)

                if label != "standard":
                    print(
                        f"    ⚠ used {label} TLS profile "
                        "(server requires relaxed settings)"
                    )

                success = True
                break

            except requests.exceptions.SSLError:

                if label != "legacy-ssl":
                    print(f"    … retrying with {attempts[attempts.index((label, verify, legacy)) + 1][0]} TLS profile")
                    continue

                print("    ✗ download failed: SSL handshake refused on all profiles")

                if os.path.exists(dest_path):
                    os.remove(dest_path)

                return None

            except requests.RequestException as exc:

                print(f"    ✗ download failed: {exc}")

                if os.path.exists(dest_path):
                    os.remove(dest_path)

                return None

        if not success:
            return None

        if not cls._is_valid_pdf(dest_path):

            print(
                f"    ✗ downloaded file is not a valid PDF "
                f"(server may have returned HTML)"
            )

            os.remove(dest_path)
            return None

        size_kb = os.path.getsize(dest_path) // 1024

        print(f"    ✓ saved {size_kb} KB")

        return captured

    @classmethod
    def _is_valid_pdf(cls, path):

        if not os.path.exists(path):
            return False

        if os.path.getsize(path) < 1024:
            return False

        with open(path, "rb") as f:

            head = f.read(4)

        return head == cls.PDF_MAGIC

    @staticmethod
    def _load_cache(cache_path):

        if not os.path.exists(cache_path):
            return {}

        try:

            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)

        except (OSError, json.JSONDecodeError):

            return {}

    @staticmethod
    def _save_cache(cache_path, cache):

        os.makedirs(os.path.dirname(cache_path), exist_ok=True)

        with open(cache_path, "w", encoding="utf-8") as f:

            json.dump(cache, f, indent=2)
