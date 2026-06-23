# GCC Incentives Tracker

A Python pipeline that builds an Excel reference workbook of Global Capability Centre (GCC) incentives across India and selected countries, sourced from official government policy PDFs and HTML pages.

## What you get

Each run produces three artifacts under `output/`, all datestamped:

| File | Contents |
|---|---|
| `gcc_incentives_global_<date>.xlsx` | One sheet per jurisdiction. 6 incentive types by 3 scope tiers per sheet. New content highlighted in red versus the previous run. |
| `gcc_sources_<date>.xlsx` | Run report. Every source URL with download status. |
| `gcc_incentives_global_<date>.xlsx` → **Summary** tab | Quick scan view. Lists only the new bullets versus the previous run. |

## Quick start

```bash
pip install -r requirements.txt
ollama pull llama3.2:3b           # one time, ~2 GB; only if Ollama is installed
python3 main_global.py
```

The first run downloads ~70 MB of policy PDFs, scrapes ~150 HTML pages, paraphrases through Ollama, and writes the workbook. Expect 15 to 30 minutes the first time. Subsequent runs are much faster thanks to caching.

## Requirements

### Mandatory

* Python 3.10+
* Packages in `requirements.txt`: `requests`, `pdfplumber`, `openpyxl`, `beautifulsoup4`, `lxml`

### Optional but recommended

* **Ollama** with `llama3.2:3b` model pulled — enables LLM paraphrasing
  * Mac: download `.pkg` from [ollama.com](https://ollama.com) or `brew install ollama`
  * Windows: download `.exe` installer from [ollama.com](https://ollama.com)
  * Then once: `ollama pull llama3.2:3b`
* **Tesseract + ocrmypdf** — enables OCR for scanned PDFs
  * Mac: `brew install tesseract ocrmypdf`
  * Windows: install Tesseract from UB Mannheim, then `pip install ocrmypdf`

If either is missing, the pipeline still runs but skips that step with a warning.

## Run modes

```bash
# Default: full pipeline with paraphrasing
python3 main_global.py

# Skip paraphrasing (faster, raw extracted text)
python3 main_global.py --nopara

# Force redownload all source PDFs
python3 main_global.py --refresh

# Use a different Ollama model
python3 main_global.py --model llama3.1:8b

# Use a different sources file
python3 main_global.py --sources path/to/other_sources.xlsx
```

## How to add or change sources

The pipeline reads all source URLs from `input/sources.xlsx`. To make changes:

1. Open `input/sources.xlsx` in Excel
2. Add, edit, or remove rows
3. Save
4. Rerun `python3 main_global.py`

No code change needed.

### Columns in `input/sources.xlsx`

| Column | Use |
|---|---|
| Active | `yes` or `no`. Toggle a source without deleting the row. |
| Region | `India` or `Global` |
| Jurisdiction | State name (e.g., Gujarat) or country name (e.g., Poland) |
| Filename | Local filename for the PDF (only for PDF sources) |
| Validity | Policy validity period shown in the output workbook |
| Source URL | Direct link to PDF or HTML page |
| Referer | Optional. Some hosts require it. |
| Notes | Free text |

## Project layout

```
gcc_news_incentive_tracker/
├── input/
│   ├── sources.xlsx              # All source URLs (editable)
│   └── template.xlsx             # Schema reference (read only)
├── sources/
│   ├── india/                    # Downloaded India PDFs (cached)
│   └── global/<country>/         # Downloaded country PDFs (cached)
├── output/
│   ├── gcc_incentives_global_<date>.xlsx
│   ├── gcc_sources_<date>.xlsx
│   └── .paraphrase_cache.json    # Ollama paraphrase cache
├── feeds/
│   ├── policy_downloader.py      # PDF fetcher with 3 tier TLS fallback
│   ├── sources_loader.py         # Reads input/sources.xlsx
│   └── previous_workbook_reader.py
├── extractor/
│   ├── policy_pdf_reader.py      # PDF text extractor + optional OCR
│   ├── policy_html_reader.py     # BeautifulSoup HTML scraper
│   ├── policy_bucketer.py        # English + Spanish keyword classifier
│   └── paraphraser.py            # Ollama HTTP client + cache
├── exporter/
│   ├── policy_excel_exporter.py  # Writes the incentives workbook
│   └── sources_excel_exporter.py # Writes the sources report
├── main_global.py                # Main entry point
├── main_india.py                 # India only entry point (legacy)
└── requirements.txt
```

## Output workbook structure

Each run produces a workbook with these tabs, in this order:

1. **Definition & Methodology** — explanatory text describing the schema
2. **Summary** — only new bullets versus the previous run, in red on pink rows
3. **India-State wise** — 8 priority states as columns
4. **Mexico, Poland, Hungary, ...** — one sheet per country, 35 in total

Every jurisdiction sheet uses the same row layout:

| Rows | Content |
|---|---|
| Row 1 | Header |
| Row 2 | Policy validity period |
| Rows 3 to 20 | 6 incentive types × 3 scope tiers |

The 6 incentive types are:

1. Financial Incentives
2. Infrastructure
3. Talent
4. Regulatory, Ease of Doing Business & Non-financial Support
5. Innovation / R&D / Patent
6. Others

The 3 scope tiers are:

1. Across the state or country (Common)
2. Specific to Tier 1 cities
3. Specific to Tier 2 & 3 cities

## How the diff works

After the first run, every subsequent run compares against the most recent prior workbook in `output/`.

* New bullets render in **red** (`#C00000`).
* Unchanged bullets render in **black**.
* The Summary sheet lists only new bullets, one per row, with a light pink background.
* On the very first run there is no baseline, so everything renders as plain text.

The diff is bullet level. Adding a new clause shows that clause in red while the rest of the cell stays black.

To force the diff to recompute from scratch, delete `output/.paraphrase_cache.json` and any old workbooks in `output/`, then rerun. The next run becomes the new baseline.

## How paraphrasing works

When Ollama is reachable on `localhost:11434` and the model is pulled, every extracted clause is sent to the LLM for a clean English paraphrase.

* Input clause: raw text from a PDF or HTML page, possibly in Spanish or Polish
* Output cell: a short English summary, 1 to 3 sentences

Paraphrased outputs are cached in `output/.paraphrase_cache.json` keyed by `sha1(model + input)`. Reruns use the cache; only changed source text triggers a new LLM call.

The cache is your **memory of past paraphrasing**. Keep it. Deleting it forces every cell to repaint as red on the next run because the new paraphrase will differ slightly from the previous one.

## Known limitations

1. The LLM occasionally alters numeric values (e.g., a `50 Cr` cap becoming `5 Cr`). Always verify against the source PDF.
2. HTML landing pages can include marketing copy alongside actual policy detail. Cells with HTML origin often need light human editing.
3. Scanned image PDFs (e.g., some Indian gazettes) need OCR. Without Tesseract installed, those cells stay empty.
4. The Mexico government servers reject connections from many networks. If Mexico cells are empty, download the PDFs manually and place them in `sources/global/mexico/`.
5. The bucketer's keyword maps cover English and Spanish. French, Polish, Portuguese, and other languages produce sparser cells.

## Troubleshooting

### Ollama not reachable

You see: `⚠ Ollama not reachable at http://localhost:11434 or model 'llama3.2:3b' not pulled.`

Fix:
1. `ollama --version` to confirm install
2. `ollama list` to confirm `llama3.2:3b` is pulled
3. Start the Ollama desktop app on Mac, or check the Ollama service on Windows
4. If you don't want to install Ollama, run with `--nopara`

### Pip can't find packages

```
pip install -r requirements.txt
```

If your `.venv` is broken, point PyCharm at the system Python instead:

* PyCharm: Settings → Project → Python Interpreter → Add → System Interpreter

### A download URL is broken

Edit the URL in `input/sources.xlsx`, save, rerun with `--refresh`.

### Mexico cells are blank

Mexican government servers refuse connections from outside Mexico. Download the PDFs manually, drop them into `sources/global/mexico/`, name them as in `input/sources.xlsx`, rerun.

### Output workbook is open in Excel, can't write

Close the file in Excel before running. The script overwrites today's file in place.

## Verification before sharing

This pipeline produces a **draft for human review**. Always:

1. Open the Summary tab. Spot check 3 to 5 new bullets against their source PDFs.
2. Sample 1 or 2 cells in each country sheet. Confirm numeric values match the source.
3. Review the Sources workbook to confirm every "Used" source URL is the canonical authoritative one.

LLM paraphrasing is fast and consistent, but it is not authoritative. Numbers and percentages must be verified before circulating the workbook externally.
