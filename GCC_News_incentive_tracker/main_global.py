import argparse
import os
from datetime import date

from feeds.policy_downloader import PolicyDownloader
from feeds.previous_workbook_reader import PreviousWorkbookReader
from feeds.sources_loader import SourcesLoader
from extractor.policy_pdf_reader import PolicyPDFReader
from extractor.policy_html_reader import PolicyHTMLReader
from extractor.policy_bucketer import PolicyBucketer
from extractor.paraphraser import OllamaParaphraser
from exporter.policy_excel_exporter import PolicyExcelExporter
from exporter.sources_excel_exporter import SourcesExcelExporter


INPUT_DIR = "input"
SOURCES_FILE = os.path.join(INPUT_DIR, "sources.xlsx")
TEMPLATE_FILE = os.path.join(INPUT_DIR, "template.xlsx")

INDIA_SOURCES_DIR = "sources/india"
GLOBAL_SOURCES_DIR = "sources/global"


def empty_buckets():

    return {
        it: {scope: [] for scope in PolicyBucketer.SCOPES}
        for it in PolicyBucketer.INCENTIVE_TYPES
    }


def state_dir_name(state):
    return state.lower().replace(" ", "_")


def country_dir_name(country):
    return country.lower().replace(" ", "_")


def ensure_pdf_sources(india_pdfs, country_pdfs, force=False):

    print("Step 1a: ensuring India PDFs\n")

    india_available = {}

    for state, pdfs in india_pdfs.items():

        downloaded = []

        for filename, url, referer in pdfs:

            dest = os.path.join(INDIA_SOURCES_DIR, filename)

            print(f"→ {state} / {filename}")

            ok = PolicyDownloader.ensure(url, dest, referer=referer, force=force)

            if ok:
                downloaded.append(dest)

        india_available[state] = downloaded

    print("\nStep 1b: ensuring country PDFs\n")

    country_available = {}

    for country, pdfs in country_pdfs.items():

        country_dir = os.path.join(GLOBAL_SOURCES_DIR, country_dir_name(country))

        downloaded = []

        for filename, url, referer in pdfs:

            dest = os.path.join(country_dir, filename)

            print(f"→ {country} / {filename}")

            ok = PolicyDownloader.ensure(url, dest, referer=referer, force=force)

            if ok:
                downloaded.append(dest)

        country_available[country] = downloaded

    return india_available, country_available


def build_india_data(india_available, india_html, india_validity, india_states):

    print("\nStep 2a: extracting India\n")

    state_data = {}

    validity_by_state = {}

    for state in india_states:

        validity_by_state[state] = india_validity.get(state, "")

        paths = india_available.get(state, [])

        html_urls = india_html.get(state, [])

        paragraphs = []

        if paths:

            print(f"→ {state}: {len(paths)} PDF(s)")

            for path in paths:

                try:
                    paragraphs.extend(PolicyPDFReader.read(path))
                except Exception as exc:
                    print(f"    ✗ {os.path.basename(path)} failed: {exc}")

        if html_urls:

            print(f"  + {len(html_urls)} HTML reference(s)")

            for url in html_urls:

                try:
                    paragraphs.extend(PolicyHTMLReader.read(url))
                except Exception:
                    pass

        if not paragraphs:

            state_data[state] = empty_buckets()
            continue

        state_data[state] = PolicyBucketer.bucket(paragraphs)

    return state_data, validity_by_state


def build_country_data(country_available, country_html, country_validity, all_countries):

    print("\nStep 2b: extracting countries\n")

    country_data = {}

    validity_by_country = {}

    for country in all_countries:

        validity_by_country[country] = country_validity.get(country, "")

        paths = country_available.get(country, [])

        html_urls = country_html.get(country, [])

        paragraphs = []

        if paths:

            print(f"→ {country}: {len(paths)} PDF(s)")

            for path in paths:

                try:
                    paragraphs.extend(PolicyPDFReader.read(path))
                except Exception as exc:
                    print(f"    ✗ {os.path.basename(path)} failed: {exc}")

        if html_urls:

            if not paths:
                print(f"→ {country}: {len(html_urls)} HTML reference(s)")

            for url in html_urls:

                try:
                    paras = PolicyHTMLReader.read(url)
                    if paras:
                        paragraphs.extend(paras)
                except Exception:
                    pass

        if not paragraphs:

            country_data[country] = empty_buckets()
            continue

        country_data[country] = PolicyBucketer.bucket(paragraphs)

        total = sum(
            len(items)
            for scopes in country_data[country].values()
            for items in scopes.values()
        )

        print(f"  bucketed {total} items from {len(paragraphs)} paragraphs")

    return country_data, validity_by_country


def build_sources_rows(srcs, india_available, country_available):

    rows = []

    for state, pdfs in srcs["india_pdfs"].items():

        downloaded = {os.path.basename(p) for p in india_available.get(state, [])}

        for filename, url, _ in pdfs:

            status = "Used" if filename in downloaded else "Failed"

            local = (
                os.path.join(INDIA_SOURCES_DIR, filename)
                if filename in downloaded else ""
            )

            note = "Downloaded and extracted" if status == "Used" else (
                "Configured but download failed"
            )

            rows.append((
                "India", state, url, "PDF", status, local, note,
            ))

    for state, urls in srcs["india_html"].items():

        for url in urls:

            rows.append((
                "India", state, url, "HTML", "Scraped", "",
                "HTML scraped and bucketed",
            ))

    for country, pdfs in srcs["country_pdfs"].items():

        downloaded = {os.path.basename(p) for p in country_available.get(country, [])}

        for filename, url, _ in pdfs:

            status = "Used" if filename in downloaded else "Failed"

            local = (
                os.path.join(GLOBAL_SOURCES_DIR, country_dir_name(country), filename)
                if filename in downloaded else ""
            )

            note = "Downloaded and extracted" if status == "Used" else (
                "Configured but download failed"
            )

            rows.append((
                "Global", country, url, "PDF", status, local, note,
            ))

    for country, urls in srcs["country_html"].items():

        for url in urls:

            rows.append((
                "Global", country, url, "HTML", "Scraped", "",
                "HTML scraped and bucketed",
            ))

    return rows


def apply_paraphrase(data, paraphraser, label):

    for jurisdiction, buckets in data.items():

        for incentive_type, scopes in buckets.items():

            for scope, items in scopes.items():

                if not items:
                    continue

                tag = f"{label}/{jurisdiction[:18]}/{incentive_type[:8]}"

                scopes[scope] = paraphraser.paraphrase_many(items, label=tag)


def _ordered_keys(*dicts):

    seen = []

    for d in dicts:

        for k in d.keys():

            if k not in seen:
                seen.append(k)

    return seen


def output_paths():

    today = date.today().isoformat()

    return (
        f"output/gcc_incentives_global_{today}.xlsx",
        f"output/gcc_sources_{today}.xlsx",
    )


def main():

    parser = argparse.ArgumentParser(
        description="Build the global GCC incentives workbook from input/sources.xlsx."
    )

    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Force re-download of all PDFs, ignoring local cache.",
    )

    parser.add_argument(
        "--sources",
        default=SOURCES_FILE,
        help=f"Path to sources workbook (default: {SOURCES_FILE})",
    )

    parser.add_argument(
        "--nopara", "--no-paraphrase",
        dest="paraphrase",
        action="store_false",
        default=True,
        help=(
            "Skip the Ollama paraphrasing step. Cells contain raw extracted "
            "text instead of LLM-cleaned summaries. Useful for quick test "
            "runs or when Ollama is not installed."
        ),
    )

    # Backwards compatible alias; paraphrase is on by default now.
    parser.add_argument(
        "--paraphrase",
        dest="paraphrase",
        action="store_true",
        help=argparse.SUPPRESS,
    )

    parser.add_argument(
        "--model",
        default=OllamaParaphraser.DEFAULT_MODEL,
        help=(
            f"Ollama model name for paraphrasing "
            f"(default: {OllamaParaphraser.DEFAULT_MODEL})"
        ),
    )

    args = parser.parse_args()

    print(f"Loading sources from {args.sources}\n")

    srcs = SourcesLoader.load(args.sources)

    india_states = _ordered_keys(
        srcs["india_pdfs"], srcs["india_html"], srcs["india_validity"]
    )

    all_countries = _ordered_keys(
        srcs["country_pdfs"], srcs["country_html"], srcs["country_validity"]
    )

    print(
        f"  → India states: {len(india_states)}\n"
        f"  → Countries: {len(all_countries)}\n"
    )

    os.makedirs(INDIA_SOURCES_DIR, exist_ok=True)
    os.makedirs(GLOBAL_SOURCES_DIR, exist_ok=True)
    os.makedirs("output", exist_ok=True)

    india_available, country_available = ensure_pdf_sources(
        srcs["india_pdfs"], srcs["country_pdfs"], force=args.refresh,
    )

    state_data, validity_by_state = build_india_data(
        india_available, srcs["india_html"], srcs["india_validity"], india_states,
    )

    country_data, validity_by_country = build_country_data(
        country_available, srcs["country_html"], srcs["country_validity"],
        all_countries,
    )

    if args.paraphrase:

        print("\nStep 2c: paraphrasing via Ollama\n")

        para = OllamaParaphraser(model=args.model)

        if not para.is_available():

            print(
                "⚠ Ollama not reachable at "
                f"{OllamaParaphraser.HOST} or model "
                f"'{args.model}' not pulled. "
                "Skipping paraphrasing. Run: "
                f"ollama pull {args.model}"
            )

        else:

            apply_paraphrase(state_data, para, "states")
            apply_paraphrase(country_data, para, "countries")

    print("\nStep 3: writing workbooks\n")

    out_path, sources_path = output_paths()

    baseline_path = PreviousWorkbookReader.find_latest(
        "output", "gcc_incentives_global_", exclude_path=out_path,
    )

    baseline = PreviousWorkbookReader.load(baseline_path)

    if baseline:
        print(f"  ⟂ comparing against baseline: {os.path.basename(baseline_path)}")
    else:
        print("  ⟂ no prior workbook found; all content rendered black")

    PolicyExcelExporter.export_global(
        state_data=state_data,
        validity_by_state=validity_by_state,
        country_data=country_data,
        validity_by_country=validity_by_country,
        placeholder_data={},
        placeholder_validity={},
        output_path=out_path,
        baseline=baseline,
    )

    print(f"  ✓ Wrote {out_path}")

    rows = build_sources_rows(srcs, india_available, country_available)

    SourcesExcelExporter.export(rows, sources_path)

    print(f"  ✓ Wrote {sources_path}")


if __name__ == "__main__":
    main()
