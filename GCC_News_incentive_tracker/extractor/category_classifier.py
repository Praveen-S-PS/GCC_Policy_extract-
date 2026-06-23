class CategoryClassifier:
    @staticmethod
    def classify(title):
        title = title.lower()
        if "policy" in title:
            return "GCC Policy"
        if "incentive" in title:
            return "Incentive"
        if "tax" in title:
            return "Tax Benefit"
        if "subsidy" in title:
            return "Subsidy"
        return "General GCC News"