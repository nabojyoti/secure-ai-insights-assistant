import re
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.agents.planner import Planner
from app.guardrails import InputGuardrail, OutputGuardrail
from app.models.db_models import ChatMessage, ToolTrace
from app.services.analytics_service import AnalyticsService
from app.tools.rag_tool import RAGTool


class AgentState(TypedDict, total=False):
    db: Session
    user: dict[str, Any]
    query: str
    sanitized_query: str
    tools: list[str]
    metrics: dict[str, Any]
    sources: list[dict[str, Any]]
    tool_status: list[str]
    answer: str
    recommendations: list[str]
    response: dict[str, Any]


class Orchestrator:
    def __init__(self):
        self.analytics = AnalyticsService()
        self.rag = RAGTool()
        self.planner = Planner()
        self.input_guardrail = InputGuardrail()
        self.output_guardrail = OutputGuardrail()
        self.graph = self._build_graph()

    def run(self, db: Session, query: str, user: dict) -> dict:
        initial_state: AgentState = {
            "db": db,
            "user": user,
            "query": query,
            "metrics": {},
            "sources": [],
            "tool_status": [],
        }
        final_state = self.graph.invoke(initial_state)
        return final_state["response"]

    def _build_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node("input_guardrail", self._input_guardrail_node)
        graph.add_node("plan", self._plan_node)
        graph.add_node("execute_tools", self._execute_tools_node)
        graph.add_node("compose", self._compose_node)
        graph.add_node("output_guardrail", self._output_guardrail_node)
        graph.add_node("persist", self._persist_node)

        graph.set_entry_point("input_guardrail")
        graph.add_edge("input_guardrail", "plan")
        graph.add_edge("plan", "execute_tools")
        graph.add_edge("execute_tools", "compose")
        graph.add_edge("compose", "output_guardrail")
        graph.add_edge("output_guardrail", "persist")
        graph.add_edge("persist", END)
        return graph.compile()

    def _input_guardrail_node(self, state: AgentState) -> AgentState:
        result = self.input_guardrail.validate(state["query"])
        state["sanitized_query"] = result.sanitized_query
        return state

    def _plan_node(self, state: AgentState) -> AgentState:
        state["tools"] = self.planner.plan(state["sanitized_query"])
        return state

    def _execute_tools_node(self, state: AgentState) -> AgentState:
        db = state["db"]
        user = state["user"]
        query = state["sanitized_query"]
        metrics = state.get("metrics", {})
        sources = state.get("sources", [])
        tool_status = state.get("tool_status", [])

        for tool in state.get("tools", []):
            try:
                if tool == "top_titles":
                    metrics[tool] = self.analytics.top_titles(db, year=self._extract_year(query) or 2025)
                    sources.append({"source_type": "sql", "name": "movies + watch_activity"})
                elif tool == "compare_titles":
                    left, right = self._extract_comparison_titles(query)
                    metrics[tool] = self.analytics.compare_titles(db, left, right)
                    sources.append({"source_type": "sql", "name": "movies + reviews + watch_activity"})
                elif tool == "strongest_city":
                    metrics[tool] = self.analytics.strongest_city(db) or {}
                    sources.append({"source_type": "sql", "name": "regional_performance"})
                elif tool == "weak_genres":
                    metrics[tool] = self.analytics.weak_genres(db)
                    sources.append({"source_type": "sql", "name": "movies + reviews + watch_activity"})
                elif tool == "audience_segments":
                    metrics[tool] = self.analytics.audience_segments(db)
                    sources.append({"source_type": "sql", "name": "viewers + watch_activity"})
                elif tool == "marketing_roi":
                    metrics[tool] = self.analytics.marketing_roi(db)
                    sources.append({"source_type": "sql", "name": "marketing_spend + watch_activity"})
                elif tool == "rag":
                    docs = self.rag.retrieve(db, query)
                    metrics["documents"] = docs
                    sources.extend(
                        {
                            "source_type": "pdf",
                            "name": doc["document_name"],
                            "snippet": doc["snippet"],
                        }
                        for doc in docs
                    )
                tool_status.append(tool)
                db.add(ToolTrace(user_id=user["sub"], query=query, tool_name=tool, status="success"))
            except Exception as exc:
                db.add(ToolTrace(user_id=user["sub"], query=query, tool_name=tool, status="error", detail=str(exc)))
                raise

        state["metrics"] = metrics
        state["sources"] = sources
        state["tool_status"] = tool_status
        return state

    def _compose_node(self, state: AgentState) -> AgentState:
        metrics = state.get("metrics", {})
        state["answer"] = self._compose_answer(metrics)
        state["recommendations"] = self._recommendations(metrics)
        state["response"] = {
            "answer": state["answer"],
            "sources": self._dedupe_sources(state.get("sources", [])),
            "metrics": metrics,
            "recommendations": state["recommendations"],
            "trace": {
                "tools_used": state.get("tool_status", []),
                "workflow": [
                    "input_guardrail",
                    "planner",
                    "approved_tools",
                    "compose",
                    "output_guardrail",
                ],
                "reasoning": (
                    "LangGraph routed the question through guardrails and approved backend tools; "
                    "SQL access is restricted to typed analytics services, not autonomous SQL generation."
                ),
            },
        }
        return state

    def _output_guardrail_node(self, state: AgentState) -> AgentState:
        result = self.output_guardrail.validate(state["response"])
        state["response"] = result.response
        return state

    def _persist_node(self, state: AgentState) -> AgentState:
        db = state["db"]
        user = state["user"]
        db.add(ChatMessage(user_id=user["sub"], query=state["sanitized_query"], answer=state["response"]["answer"]))
        db.commit()
        return state

    def _compose_answer(self, metrics: dict) -> str:
        if "compare_titles" in metrics:
            rows = metrics["compare_titles"]
            if len(rows) >= 2:
                winner = max(rows, key=lambda row: row["revenue"])
                return f"{winner['title']} leads the comparison on revenue, with {winner['views']} views and a {winner['completion_rate']:.1%} completion rate."

        if "top_titles" in metrics and metrics["top_titles"]:
            top = metrics["top_titles"][0]
            return f"{top['title']} is the strongest title in the selected period, generating {top['revenue']:.2f} revenue across {top['views']} views."

        if "strongest_city" in metrics and metrics["strongest_city"]:
            city = metrics["strongest_city"]
            return f"{city['city']} has the strongest city engagement with a {city['engagement_score']} engagement score."

        if "weak_genres" in metrics and metrics["weak_genres"]:
            weak = metrics["weak_genres"][0]
            return f"{weak['genre']} is the weakest observed genre by views, with {weak['views']} views and average rating {weak['avg_rating']}."

        if "audience_segments" in metrics and metrics["audience_segments"]:
            segment = metrics["audience_segments"][0]
            return f"{segment['segment']} is the most engaged audience segment by revenue, with {segment['views']} views and {segment['watch_minutes']} watch minutes."

        if "marketing_roi" in metrics and metrics["marketing_roi"]:
            roi = metrics["marketing_roi"][0]
            return f"{roi['title']} has the strongest observed campaign return in the current data, led by {roi['channel']}."

        if "documents" in metrics and metrics["documents"]:
            return f"The internal reports point to this driver: {metrics['documents'][0]['snippet']}"

        return "The available approved sources did not contain enough evidence for a confident answer."

    def _recommendations(self, metrics: dict) -> list[str]:
        recommendations = []
        if "top_titles" in metrics and metrics["top_titles"]:
            recommendations.append(f"Prioritize retention and cross-promotion around {metrics['top_titles'][0]['title']}.")
        if "weak_genres" in metrics and metrics["weak_genres"]:
            recommendations.append(f"Review positioning and creative quality for {metrics['weak_genres'][0]['genre']} content.")
        if "audience_segments" in metrics and metrics["audience_segments"]:
            recommendations.append(f"Target {metrics['audience_segments'][0]['segment']} with the next campaign test.")
        if "documents" in metrics:
            recommendations.append("Use document-backed qualitative context before committing leadership actions.")
        return recommendations or ["Seed or ingest more data before making a major decision."]

    def _extract_year(self, query: str) -> int | None:
        match = re.search(r"\b(20\d{2})\b", query)
        return int(match.group(1)) if match else None

    def _extract_comparison_titles(self, query: str) -> tuple[str, str]:
        match = re.search(r"compare\s+(.+?)\s+(?:vs|versus|and)\s+(.+?)[?.!]*$", query, flags=re.I)
        if not match:
            match = re.search(r"(.+?)\s+vs\s+(.+?)[?.!]*$", query, flags=re.I)
        if match:
            return match.group(1).strip().title(), match.group(2).strip().title()
        return "Dark Orbit", "Last Kingdom"

    def _dedupe_sources(self, sources: list[dict]) -> list[dict]:
        seen = set()
        unique = []
        for source in sources:
            key = (source.get("source_type"), source.get("name"), source.get("snippet"))
            if key not in seen:
                unique.append(source)
                seen.add(key)
        return unique
