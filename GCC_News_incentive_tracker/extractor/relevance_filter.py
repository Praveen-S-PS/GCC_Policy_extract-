class RelevanceFilter:

    GCC_KEYWORDS = [

        "global capability centre",
        "global capability center",

        "gcc policy",
        "gcc incentive",

        "global capability centre policy",
        "global capability center policy",

        "shared services",
        "global business services",

        "gcc"
    ]

    @classmethod
    def is_relevant(cls, title):

        title = title.lower()

        return any(
            keyword in title
            for keyword in cls.GCC_KEYWORDS
        )