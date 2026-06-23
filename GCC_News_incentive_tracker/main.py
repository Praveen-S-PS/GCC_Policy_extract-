from config import RSS_URL
from feeds.rss_reader import RSSReader
from extractor.relevance_filter import RelevanceFilter
from extractor.location_extractor import LocationExtractor
from extractor.category_classifier import CategoryClassifier
from extractor.policy_classifier import PolicyClassifier
from extractor.incentive_classifier import IncentiveClassifier
from extractor.metric_extractor import MetricExtractor

from database.sqlite_manager import SQLiteManager
from exporter.excel_exporter import ExcelExporter


def main():

    reader = RSSReader(RSS_URL)

    db = SQLiteManager()

    articles = reader.get_articles()

    print(f"\nFound {len(articles)} articles\n")

    new_records = 0

    for article in articles:

        title = article["title"]

        # Skip non-GCC articles
        if not RelevanceFilter.is_relevant(title):
            continue

        state = LocationExtractor.get_state(title)

        country = LocationExtractor.get_country(title)

        category = CategoryClassifier.classify(title)

        policy_type = PolicyClassifier.classify(title)

        incentive_type = IncentiveClassifier.classify(title)

        jobs = MetricExtractor.extract_jobs(title)

        investment = MetricExtractor.extract_investment(title)

        record = {

            "title": title,

            "country": country,

            "state": state,

            "category": category,

            "policy_type": policy_type,

            "incentive_type": incentive_type,

            "jobs": jobs,

            "investment": investment,

            "source": article["source_name"],

            "site": article["source_site"],

            "date": article["published"]

        }

        if not db.article_exists(title):

            db.insert(record)

            new_records += 1

            print(f"✓ Added: {title}")

        else:

            print(f"↺ Already Exists: {title}")

    print(f"\nNew Articles Added : {new_records}")

    all_records = db.get_all()

    ExcelExporter.export(all_records)

    print(
        f"Exported {len(all_records)} records to output/gcc_tracker.xlsx"
    )


if __name__ == "__main__":
    main()