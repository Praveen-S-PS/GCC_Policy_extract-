class PolicyClassifier:

    @staticmethod
    def classify(title):

        title = title.lower()

        if any(
            word in title
            for word in [
                "launches",
                "launched",
                "unveils",
                "unveiled",
                "approves",
                "approved",
                "clears",
                "cleared"
            ]
        ):
            return "New Policy"

        if "target" in title:
            return "Investment Target"

        if "jobs" in title:
            return "Employment Target"

        return "General GCC News"