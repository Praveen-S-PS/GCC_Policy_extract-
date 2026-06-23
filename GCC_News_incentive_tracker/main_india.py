import argparse
import os
from datetime import date

from feeds.policy_downloader import PolicyDownloader
from extractor.policy_pdf_reader import PolicyPDFReader
from extractor.policy_bucketer import PolicyBucketer
from exporter.policy_excel_exporter import PolicyExcelExporter


SOURCES_DIR = "sources/india"
OUTPUT_PATH = f"output/gcc_incentives_india_{date.today().isoformat()}.xlsx"


# state, filename, validity, source URL, referer (optional)
# Sources mirror those used in the expected workbook where available.
STATE_SOURCES = [
    (
        "Gujarat",
        "gujarat.pdf",
        "Feb 2025 – Mar 2030",
        "https://api.giftgujarat.in/public/GCC_Policy.pdf",
        None,
    ),
    (
        "Karnataka",
        "karnataka.pdf",
        "2024 – 2029",
        "https://eitbt.karnataka.gov.in/uploads/media_to_upload1732030878.pdf",
        None,
    ),
    (
        "Madhya Pradesh",
        "madhya_pradesh.pdf",
        "Feb 2025 – Feb 2030",
        "https://mpsedc.mp.gov.in/Uploaded%20Document/UpcomingEvents/10122024030121Madhya%20Pradesh%20GCC%20Policy%202024.pdf",
        None,
    ),
    (
        "Maharashtra",
        "maharashtra.pdf",
        "Nov 2025 – Mar 2030",
        "https://industry.maharashtra.gov.in/sites/default/files/2025-09/gcc-policy-paraesa-naota-english.pdf",
        None,
    ),
    (
        "Rajasthan",
        "rajasthan.pdf",
        "2025 – Mar 2029",
        "https://avantiscdnprodstorage.blob.core.windows.net/legalupdatedocs/50160/Rajasthan-Govt.-issued-the-Global-Capability-Center-Policy-2025-dec022025.pdf",
        None,
    ),
    (
        "Tamil Nadu",
        None,
        "Apr 2024 – Mar 2027",
        None,
        None,
    ),
    (
        "Telangana",
        "telangana.pdf",
        "2023 – 2028",
        "https://gccrise.com/wp-content/uploads/2025/01/Nasscom-GCC-Telangana-Playbook-Nov-2024.pdf",
        None,
    ),
    (
        "Uttar Pradesh",
        "uttar_pradesh.pdf",
        "Jun 2025 – Jun 2030",
        "https://invest.up.gov.in/wp-content/uploads/2025/06/GCC-Policy-Eng_050625.pdf",
        None,
    ),
]


def empty_buckets():

    return {
        it: {scope: [] for scope in PolicyBucketer.SCOPES}
        for it in PolicyBucketer.INCENTIVE_TYPES
    }


def ensure_sources(force=False):

    print("Step 1: ensuring source PDFs are present\n")

    available = {}

    for state, filename, _, url, referer in STATE_SOURCES:

        if filename is None or url is None:

            print(f"⊝ {state}: no public source configured, skipping")
            available[state] = False
            continue

        print(f"→ {state}")

        dest = os.path.join(SOURCES_DIR, filename)

        ok = PolicyDownloader.ensure(
            url, dest, referer=referer, force=force
        )

        available[state] = ok

    return available


def build_state_data(available):

    print("\nStep 2: extracting and bucketing\n")

    state_data = {}

    validity_by_state = {}

    for state, filename, validity, _, _ in STATE_SOURCES:

        validity_by_state[state] = validity

        if not available.get(state) or filename is None:

            state_data[state] = empty_buckets()
            print(f"⊝ {state}: no PDF, columns will be empty")
            continue

        pdf_path = os.path.join(SOURCES_DIR, filename)

        print(f"→ {state}: reading {filename}")

        paragraphs = PolicyPDFReader.read(pdf_path)

        buckets = PolicyBucketer.bucket(paragraphs)

        state_data[state] = buckets

        total = sum(
            len(items)
            for scopes in buckets.values()
            for items in scopes.values()
        )

        print(f"  bucketed {total} items from {len(paragraphs)} paragraphs")

    return state_data, validity_by_state


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Build the India GCC incentives workbook. "
            "Source PDFs are auto downloaded on first run. "
            "On subsequent runs, the script checks each URL via HTTP HEAD "
            "and re-downloads only if the policy has been updated upstream."
        )
    )

    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Force re-download of all PDFs, ignoring local cache.",
    )

    args = parser.parse_args()

    os.makedirs(SOURCES_DIR, exist_ok=True)
    os.makedirs("output", exist_ok=True)

    available = ensure_sources(force=args.refresh)

    state_data, validity_by_state = build_state_data(available)

    print("\nStep 3: writing workbook\n")

    PolicyExcelExporter.export(
        state_data, validity_by_state, OUTPUT_PATH
    )

    print(f"✓ Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
