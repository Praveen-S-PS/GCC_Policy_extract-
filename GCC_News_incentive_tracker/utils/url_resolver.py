from googlesearch import search


class URLResolver:

    @staticmethod
    def get_article_url(title, source_site):

        try:

            domain = source_site.replace(
                "https://",
                ""
            ).replace(
                "http://",
                ""
            ).replace(
                "www.",
                ""
            )

            query = f'"{title}" site:{domain}'

            results = search(
                query,
                num_results=5
            )

            for url in results:

                return url

        except Exception as e:

            print(
                f"Resolver Error : {e}"
            )

        return None