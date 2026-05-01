import re


class Planner:
    greeting_pattern = re.compile(r"^(hi|hello|hey|yo|hola|namaste|thanks|thank you)[!. ]*$", re.I)

    def plan(self, query: str) -> list[str]:
        q = query.lower()
        tools: list[str] = []

        if self.greeting_pattern.fullmatch(query.strip()):
            return ["smalltalk"]

        wants_explanation = any(term in q for term in ["why", "trend", "trending", "explain"])
        wants_recommendation = any(term in q for term in ["recommendation", "recommendations", "leadership", "actions", "next quarter"])
        asks_weak_performance = "weak" in q or "comedy" in q

        if any(term in q for term in ["best", "top", "performed", "titles", "movies"]):
            tools.append("top_titles")
        if "compare" in q or re.search(r"\bvs\b", q):
            tools.append("compare_titles")
        if "city" in q or "regional" in q:
            tools.append("strongest_city")
        if asks_weak_performance or "genre" in q:
            tools.append("weak_genres")
        if "segment" in q or "audience" in q or "engaged" in q:
            tools.append("audience_segments")
        if "marketing" in q or "roi" in q or "campaign" in q:
            tools.append("marketing_roi")

        if wants_explanation and not any(tool in tools for tool in ["top_titles", "compare_titles", "weak_genres"]):
            tools.append("top_titles")

        if wants_recommendation:
            for tool in ["top_titles", "weak_genres", "audience_segments", "marketing_roi"]:
                tools.append(tool)

        if wants_explanation or wants_recommendation or asks_weak_performance:
            tools.append("rag")

        if not tools:
            tools.append("rag")

        return list(dict.fromkeys(tools))
