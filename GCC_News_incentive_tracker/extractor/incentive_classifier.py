class IncentiveClassifier:

    @staticmethod
    def classify(title):

        title = title.lower()

        if "tax" in title:
            return "Tax Incentive"

        if "grant" in title:
            return "Grant"

        if "subsidy" in title:
            return "Subsidy"

        if "rebate" in title:
            return "Rebate"

        if "policy" in title:
            return "Policy"

        if "investment" in title:
            return "Investment Promotion"

        return "General"

