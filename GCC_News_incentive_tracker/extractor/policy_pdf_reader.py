import os
import shutil
import subprocess

import pdfplumber
import re


class PolicyPDFReader:

    PAGE_NUM_RE = re.compile(r"^Page\s+\d+\s+of\s+\d+\s*$", re.IGNORECASE)
    HEADING_RE = re.compile(r"^\s*(\d+(?:\.\d+)*)\.?\s+([^\d].{2,200})$")
    BULLET_RE = re.compile(r"^\s*(?:[•\-\*]|[A-Za-z]\)|\d+\))\s+")

    OCR_THRESHOLD_CHARS_PER_PAGE = 30

    @classmethod
    def read(cls, pdf_path):

        text_per_page = cls._extract_pages(pdf_path)

        avg_chars = (
            sum(len(t) for t in text_per_page) / max(1, len(text_per_page))
        )

        if avg_chars < cls.OCR_THRESHOLD_CHARS_PER_PAGE:

            ocr_path = cls._try_ocr(pdf_path)

            if ocr_path:
                print(f"    ↻ used OCR for {os.path.basename(pdf_path)}")
                text_per_page = cls._extract_pages(ocr_path)

        raw_lines = []

        for text in text_per_page:

            for line in text.split("\n"):

                line = line.rstrip()

                if cls.PAGE_NUM_RE.match(line):
                    continue

                raw_lines.append(line)

        return cls._to_paragraphs(raw_lines)

    @staticmethod
    def _extract_pages(pdf_path):

        with pdfplumber.open(pdf_path) as pdf:

            return [(p.extract_text() or "") for p in pdf.pages]

    @staticmethod
    def _try_ocr(pdf_path):

        if not shutil.which("ocrmypdf"):
            return None

        ocr_path = pdf_path.replace(".pdf", ".ocr.pdf")

        if os.path.exists(ocr_path):
            return ocr_path

        try:

            subprocess.run(
                [
                    "ocrmypdf", "--skip-text", "--optimize", "1",
                    "--quiet", pdf_path, ocr_path,
                ],
                check=True,
                timeout=600,
            )

            return ocr_path

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):

            return None

    @classmethod
    def _to_paragraphs(cls, lines):

        paragraphs = []

        current_heading = ""

        current_buffer = []

        def flush():

            if current_buffer:

                text = " ".join(b.strip() for b in current_buffer if b.strip())

                if text and len(text) > 15:

                    paragraphs.append({
                        "heading": current_heading,
                        "text": text
                    })

        for line in lines:

            stripped = line.strip()

            if not stripped:

                flush()
                current_buffer = []
                continue

            m = cls.HEADING_RE.match(line)

            if m and len(stripped) < 100 and not cls.BULLET_RE.match(line):

                flush()
                current_buffer = []
                current_heading = f"{m.group(1)} {m.group(2)}".strip()

                continue

            current_buffer.append(stripped)

        flush()

        return paragraphs
