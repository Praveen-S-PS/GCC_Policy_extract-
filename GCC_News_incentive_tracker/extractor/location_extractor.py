import re


class LocationExtractor:
    COUNTRIES = [

        "India",
        "Saudi Arabia",
        "United Arab Emirates",
        "UAE",
        "Vietnam",
        "Malaysia",
        "Philippines",
        "Poland",
        "Hungary",
        "Romania",
        "Mexico",
        "Costa Rica",
        "Egypt",
        "South Africa"
    ]

    STATES = [

        "Karnataka",
        "Tamil Nadu",
        "Maharashtra",
        "Gujarat",
        "Odisha",
        "Uttar Pradesh",
        "Madhya Pradesh",
        "Telangana",
        "Andhra Pradesh",
        "Kerala",
        "West Bengal",
        "Haryana"
    ]

    @classmethod
    def get_state(cls, text):

        for state in cls.STATES:

            if state.lower() in text.lower():

                return state

        return ""

    # @classmethod
    # def get_country(cls, text):
    #
    #     if any(
    #         state.lower() in text.lower()
    #         for state in cls.STATES
    #     ):
    #         return "India"
    #
    #     return ""

    @classmethod
    def get_country(cls, text):

        text = text.lower()

        for country in cls.COUNTRIES:

            if country.lower() in text:
                return country

        if any(
                state.lower() in text
                for state in cls.STATES
        ):
            return "India"

        return ""