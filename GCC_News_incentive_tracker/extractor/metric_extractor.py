import re


class MetricExtractor:

    @staticmethod
    def extract_jobs(text):

        patterns = [

            r'([\d,]+\s*jobs)',

            r'([\d\.]+\s*lakh\s*jobs?)',

            r'([\d\.]+\s*million\s*jobs?)'

        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:

                return match.group(1)

        return ""

    @staticmethod
    def extract_investment(text):

        patterns = [

            r'₹\s?[\d,]+\s*cr',

            r'₹\s?[\d,]+\s*crore',

            r'\$[\d,]+\s*million',

            r'\$[\d,]+\s*billion'

        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:

                return match.group(0)

        return ""