import feedparser

class RSSReader:

    def __init__(self, rss_url):

        self.rss_url = rss_url

    def get_articles(self):

        feed = feedparser.parse(self.rss_url)

        articles = []

        for entry in feed.entries:

            source_name = ""

            source_site = ""

            if hasattr(entry, "source"):

                source_name = entry.source.get(
                    "title",
                    ""
                )

                source_site = entry.source.get(
                    "href",
                    ""
                )

            articles.append({

                "title": entry.get(
                    "title",
                    ""
                ),

                "published": entry.get(
                    "published",
                    ""
                ),

                "source_name": source_name,

                "source_site": source_site,

                "google_link": entry.get(
                    "link",
                    ""
                )

            })

        return articles