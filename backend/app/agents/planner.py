import re


class Planner:
    greeting_pattern = re.compile(r"^(hi|hello|hey|yo|hola|namaste|thanks|thank you)[!. ]*$", re.I)

    def plan(self, query: str) -> list[str]:
        q = query.lower()
        tools: list[str] = []

        if self.greeting_pattern.fullmatch(query.strip()):
            return ["smalltalk"]

        if any(term in q for term in ["best", "top", "performed", "titles", "movies"]):
            tools.append("top_titles")
        if "compare" in q or re.search(r"\bvs\b", q):
            tools.append("compare_titles")
        if "city" in q or "regional" in q:
            tools.append("strongest_city")
        if "weak" in q or "comedy" in q or "genre" in q:
            tools.append("weak_genres")
        if "segment" in q or "audience" in q or "engaged" in q:
            tools.append("audience_segments")
        if "marketing" in q or "roi" in q or "campaign" in q:
            tools.append("marketing_roi")
        if any(term in q for term in ["why", "trend", "trending", "explain", "recommendation", "leadership"]):
            tools.append("rag")

        if not tools:
            tools.append("rag")

        return list(dict.fromkeys(tools))
