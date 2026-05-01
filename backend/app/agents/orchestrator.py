import re
import time
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.agents.planner import Planner
from app.common_utils.logging_utils import logger
from app.guardrails import InputGuardrail, OutputGuardrail
from app.models.db_models import ChatMessage, ToolTrace
from app.services.analytics_service import AnalyticsService
from app.services.answer_synthesizer import AnswerSynthesizer
from app.services.evidence_service import EvidenceService
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
    evidence: dict[str, Any]
    response: dict[str, Any]


class Orchestrator:
    def __init__(self):
        self.analytics = AnalyticsService()
        self.rag = RAGTool()
        self.evidence_service = EvidenceService()
        self.answer_synthesizer = AnswerSynthesizer()
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
        graph.add_node("build_evidence", self._build_evidence_node)
        graph.add_node("compose", self._compose_node)
        graph.add_node("synthesize", self._synthesize_node)
        graph.add_node("output_guardrail", self._output_guardrail_node)
        graph.add_node("persist", self._persist_node)

        graph.set_entry_point("input_guardrail")
        graph.add_edge("input_guardrail", "plan")
        graph.add_edge("plan", "execute_tools")
        graph.add_edge("execute_tools", "build_evidence")
        graph.add_edge("build_evidence", "compose")
        graph.add_edge("compose", "synthesize")
        graph.add_edge("synthesize", "output_guardrail")
        graph.add_edge("output_guardrail", "persist")
        graph.add_edge("persist", END)
        return graph.compile()

    def _input_guardrail_node(self, state: AgentState) -> AgentState:
        logger.info(f"🛡️  Input Guardrail: Validating query")
        result = self.input_guardrail.validate(state["query"])
        state["sanitized_query"] = result.sanitized_query
        logger.debug(f"✓ Sanitized query: {result.sanitized_query}")
        return state

    def _plan_node(self, state: AgentState) -> AgentState:
        logger.info(f"📋 Planning: Analyzing query to select tools")
        state["tools"] = self.planner.plan(state["sanitized_query"])
        logger.info(f"🔧 Tools selected: {state['tools']}")
        return state

    def _execute_tools_node(self, state: AgentState) -> AgentState:
        db = state["db"]
        user = state["user"]
        query = state["sanitized_query"]
        metrics = state.get("metrics", {})
        sources = state.get("sources", [])
        tool_status = state.get("tool_status", [])

        logger.info(f"⚙️  Executing {len(state.get('tools', []))} tool(s)...")
        for tool in state.get("tools", []):
            tool_start = time.time()
            try:
                logger.debug(f"→ Executing tool: {tool}")
                if tool == "smalltalk":
                    metrics["smalltalk"] = {"intent": "greeting"}
                    logger.debug(f"✓ Smalltalk handled")
                elif tool == "top_titles":
                    year = self._extract_year(query) or 2025
                    logger.debug(f"→ Querying top titles for year {year}")
                    metrics[tool] = self.analytics.top_titles(db, year=year)
                    sources.append({"source_type": "sql", "name": "movies + watch_activity"})
                    logger.info(f"✓ Found {len(metrics[tool])} top titles")
                elif tool == "compare_titles":
                    left, right = self._extract_comparison_titles(query)
                    logger.debug(f"→ Comparing '{left}' vs '{right}'")
                    metrics[tool] = self.analytics.compare_titles(db, left, right)
                    sources.append({"source_type": "sql", "name": "movies + reviews + watch_activity"})
                    logger.info(f"✓ Comparison complete")
                elif tool == "strongest_city":
                    logger.debug(f"→ Finding strongest city by engagement")
                    metrics[tool] = self.analytics.strongest_city(db) or {}
                    sources.append({"source_type": "sql", "name": "regional_performance"})
                    logger.info(f"✓ Strongest city identified")
                elif tool == "weak_genres":
                    logger.debug(f"→ Analyzing weak genre performance")
                    metrics[tool] = self.analytics.weak_genres(db)
                    sources.append({"source_type": "sql", "name": "movies + reviews + watch_activity"})
                    logger.info(f"✓ Found {len(metrics[tool])} weak genres")
                elif tool == "audience_segments":
                    logger.debug(f"→ Analyzing audience segments")
                    metrics[tool] = self.analytics.audience_segments(db)
                    sources.append({"source_type": "sql", "name": "viewers + watch_activity"})
                    logger.info(f"✓ Analyzed audience segments")
                elif tool == "marketing_roi":
                    logger.debug(f"→ Calculating marketing ROI")
                    metrics[tool] = self.analytics.marketing_roi(db)
                    sources.append({"source_type": "sql", "name": "marketing_spend + watch_activity"})
                    logger.info(f"✓ Marketing ROI calculated")
                elif tool == "rag":
                    logger.debug(f"→ Retrieving relevant PDF documents")
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
                    logger.info(f"✓ Retrieved {len(docs)} PDF documents")
                tool_status.append(tool)
                db.add(ToolTrace(user_id=user["sub"], query=query, tool_name=tool, status="success"))
                elapsed = time.time() - tool_start
                logger.debug(f"✓ Tool '{tool}' completed in {elapsed:.2f}s")
            except Exception as exc:
                elapsed = time.time() - tool_start
                logger.error(f"❌ Tool '{tool}' failed in {elapsed:.2f}s: {str(exc)}")
                db.add(ToolTrace(user_id=user["sub"], query=query, tool_name=tool, status="error", detail=str(exc)))
                raise

        state["metrics"] = metrics
        state["sources"] = sources
        state["tool_status"] = tool_status
        logger.info(f"✅ All tools executed | Sources collected: {len(sources)}")
        return state

    def _build_evidence_node(self, state: AgentState) -> AgentState:
        logger.info(f"📚 Building evidence layer")
        state["evidence"] = self.evidence_service.build(
            question=state["sanitized_query"],
            metrics=state.get("metrics", {}),
            sources=state.get("sources", []),
        )
        logger.debug(f"✓ Evidence built with {len(state['evidence'].get('citations', []))} citations")
        return state

    def _compose_node(self, state: AgentState) -> AgentState:
        logger.info(f"💭 Composing answer from metrics")
        metrics = state.get("metrics", {})
        state["answer"] = self._compose_answer(metrics)
        state["recommendations"] = self._recommendations(metrics)
        logger.debug(f"✓ Answer composed | Recommendations: {len(state['recommendations'])}")
        return state

    def _synthesize_node(self, state: AgentState) -> AgentState:
        logger.info(f"✨ Synthesizing final answer")
        metrics = state.get("metrics", {})
        synthesized = self.answer_synthesizer.synthesize(
            question=state["sanitized_query"],
            evidence=state.get("evidence", {}),
            fallback_answer=state["answer"],
            fallback_recommendations=state["recommendations"],
        )
        engine = synthesized["synthesis_engine"]
        is_openai = "openai" in engine.lower()
        logger.info(f"🎯 Synthesis Engine: {engine} | Using OpenAI: {is_openai} | Confidence: {synthesized['confidence']}")
        state["response"] = {
            "answer": synthesized["answer"],
            "sources": self._dedupe_sources(state.get("sources", [])),
            "metrics": metrics,
            "recommendations": synthesized["recommendations"],
            "trace": {
                "tools_used": state.get("tool_status", []),
                "workflow": [
                    "input_guardrail",
                    "planner",
                    "approved_tools",
                    "evidence_builder",
                    "compose",
                    "answer_synthesizer",
                    "output_guardrail",
                ],
                "synthesis_engine": synthesized["synthesis_engine"],
                "confidence": synthesized["confidence"],
                "reasoning": (
                    "LangGraph routed the question through guardrails and approved backend tools; "
                    "evidence was normalized before answer synthesis; SQL access is restricted to typed analytics services, "
                    "not autonomous SQL generation."
                ),
            },
        }
        logger.debug(f"✓ Response object built | trace.synthesis_engine: {state['response']['trace']['synthesis_engine']}")
        logger.debug(f"✓ Final answer synthesized (length: {len(synthesized['answer'])} chars)")
        return state

    def _output_guardrail_node(self, state: AgentState) -> AgentState:
        logger.info(f"🛡️  Output Guardrail: Validating response safety")
        result = self.output_guardrail.validate(state["response"])
        state["response"] = result.response
        logger.debug(f"✓ Response passed safety validation")
        return state

    def _persist_node(self, state: AgentState) -> AgentState:
        logger.info(f"💾 Persisting chat message to database")
        db = state["db"]
        user = state["user"]
        db.add(ChatMessage(user_id=user["sub"], query=state["sanitized_query"], answer=state["response"]["answer"]))
        db.commit()
        logger.info(f"✓ Chat message persisted for user={user['sub']}")
        return state

    def _compose_answer(self, metrics: dict) -> str:
        if "smalltalk" in metrics:
            return "Hi. I can help with internal entertainment analytics across SQL data, CSV business files, and PDF reports. Try asking which titles performed best in 2025 or why Stellar Run is trending."

        if "documents" in metrics and "weak_genres" in metrics and metrics["weak_genres"]:
            weak = metrics["weak_genres"][0]
            snippet = metrics["documents"][0]["snippet"] if metrics["documents"] else "internal reports provide qualitative context."
            return (
                f"{weak['genre']} is the weakest observed genre by views, with {weak['views']} views, "
                f"{weak['revenue']} revenue, and average rating {weak['avg_rating']}. "
                f"PDF context adds: {snippet}"
            )

        if "documents" in metrics and "top_titles" in metrics and metrics["top_titles"]:
            top = metrics["top_titles"][0]
            snippet = metrics["documents"][0]["snippet"] if metrics["documents"] else "internal reports provide qualitative context."
            return (
                f"{top['title']} leads the selected period with {top['revenue']:.2f} revenue across "
                f"{top['views']} views and a {top['completion_rate']:.1%} completion rate. "
                f"PDF context adds: {snippet}"
            )

        if "documents" in metrics and "marketing_roi" in metrics and metrics["marketing_roi"]:
            roi = metrics["marketing_roi"][0]
            snippet = metrics["documents"][0]["snippet"] if metrics["documents"] else "internal reports provide qualitative context."
            return (
                f"{roi['title']} has the strongest observed campaign return, led by {roi['channel']}. "
                f"PDF context adds: {snippet}"
            )

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
