import re
from sqlalchemy import text
from sqlalchemy.orm import Session

FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|truncate|grant|revoke|create|attach|copy|execute)\b|--|/\*|;", re.I)


def validate_select(sql: str) -> str:
    candidate = sql.strip()
    if not re.match(r"^(select|with)\b", candidate, re.I) or FORBIDDEN.search(candidate):
        raise ValueError("Only a single read-only SELECT query is permitted.")
    if "limit" not in candidate.lower():
        candidate += " LIMIT 200"
    return candidate


def generate_sql(question: str) -> str:
    q = question.lower()
    if "total sales" in q or "sales" in q:
        return "SELECT COALESCE(SUM(amount), 0) AS total_sales FROM sales"
    if "by region" in q:
        return "SELECT region, SUM(amount) AS total_sales FROM sales GROUP BY region ORDER BY total_sales DESC"
    if "customers" in q:
        return "SELECT customer, region, amount, sold_at FROM sales ORDER BY sold_at DESC"
    return "SELECT id, customer, region, amount, sold_at FROM sales ORDER BY sold_at DESC"


def run(question: str, db: Session) -> tuple[str, list[dict], str]:
    sql = validate_select(generate_sql(question))
    result = db.execute(text(sql))
    rows = [dict(row._mapping) for row in result]
    return sql, rows, f"I ran a read-only analytics query and found {len(rows)} result row(s)."
