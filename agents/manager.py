from typing import Literal, TypedDict
from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session
from agents import document_agent, sql_agent

Intent = Literal["document", "sql", "hybrid", "report"]


def classify(question: str) -> Intent:
    lower = question.lower()
    sql_words = ("sales", "revenue", "total", "database", "customer", "region", "show ")
    document_words = ("policy", "document", "handbook", "what is", "explain", "according")
    has_sql, has_docs = any(word in lower for word in sql_words), any(word in lower for word in document_words)
    if has_sql and has_docs:
        return "hybrid"
    return "sql" if has_sql else "document"


class AgentState(TypedDict, total=False):
    question: str
    user_id: int
    db: Session
    intent: Intent
    answer: str
    confidence: float | None
    citations: list[dict]
    sql: str | None
    rows: list[dict]


def _route(state: AgentState) -> AgentState:
    return {"intent": classify(state["question"]), "answer": "", "citations": [], "confidence": None, "sql": None, "rows": []}


def _document(state: AgentState) -> AgentState:
    result = document_agent.run(state["question"], state["user_id"], state["db"])
    return result


def _sql(state: AgentState) -> AgentState:
    sql, rows, summary = sql_agent.run(state["question"], state["db"])
    prefix = state.get("answer", "")
    return {"sql": sql, "rows": rows, "answer": (prefix + "\n\n" if prefix else "") + summary}


def _next_after_route(state: AgentState) -> str:
    return {"document": "document", "sql": "sql", "hybrid": "document"}[state["intent"]]


def _next_after_document(state: AgentState) -> str:
    return "sql" if state["intent"] == "hybrid" else "end"


def _build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("route", _route)
    graph.add_node("document", _document)
    graph.add_node("sql", _sql)
    graph.add_edge(START, "route")
    graph.add_conditional_edges("route", _next_after_route, {"document": "document", "sql": "sql"})
    graph.add_conditional_edges("document", _next_after_document, {"sql": "sql", "end": END})
    graph.add_edge("sql", END)
    return graph.compile()


WORKFLOW = _build_graph()


def run_workflow(question: str, user_id: int, db: Session) -> dict:
    """Execute the manager's explicit, inspectable LangGraph workflow."""
    return WORKFLOW.invoke({"question": question, "user_id": user_id, "db": db})
