"""Guard for text-to-SQL: the LLM writes SQL, code decides whether it may run.

Defence in depth: (1) this validator, (2) a read-only database connection, (3) a row limit and a timeout.
The validator alone is not enough (SQL is a big language); the read-only connection alone gives bad errors.
"""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field

FORBIDDEN = {"insert", "update", "delete", "drop", "alter", "create", "replace", "truncate", "attach", "detach",
             "pragma", "vacuum", "grant", "revoke", "merge", "call", "exec", "execute", "copy", "reindex"}
_STRING = re.compile(r"'(?:[^']|'')*'")
_COMMENT = re.compile(r"--[^\n]*|/\*.*?\*/", re.S)
_TABLE = re.compile(r"\b(?:from|join)\s+([A-Za-z_][\w.]*)", re.I)
_LIMIT = re.compile(r"\blimit\s+(\d+)", re.I)


@dataclass
class SQLVerdict:
    ok: bool
    sql: str
    problems: list[str] = field(default_factory=list)


def check_sql(sql: str, allowed_tables: set[str], max_rows: int = 200) -> SQLVerdict:
    """Single SELECT/WITH statement, only allowed tables, no write keywords; adds or caps LIMIT."""
    problems = []
    body = _COMMENT.sub(" ", sql).strip().rstrip(";").strip()
    # keywords inside string literals do not count; same length, so positions in scan are positions in body
    scan = _STRING.sub(lambda m: "'" + "x" * (len(m.group()) - 2) + "'", body)
    if ";" in scan:
        problems.append("multiple statements")
    first = scan.split(None, 1)[0].lower() if scan else ""
    if first not in ("select", "with"):
        problems.append(f"only SELECT is allowed (got {first or 'nothing'})")
    words = set(re.findall(r"[a-z_]+", scan.lower()))
    if words & FORBIDDEN:
        problems.append("forbidden keyword: " + ", ".join(sorted(words & FORBIDDEN)))
    ctes = {m.lower() for m in re.findall(r"(?:with|,)\s*([A-Za-z_]\w*)\s+as\s*\(", scan, re.I)}
    tables = {t.split(".")[-1].lower() for t in _TABLE.findall(scan)} - ctes
    allowed = {t.lower() for t in allowed_tables}
    if tables - allowed:
        problems.append("table not allowed: " + ", ".join(sorted(tables - allowed)))
    m = next(reversed(list(_LIMIT.finditer(scan))), None)   # the last LIMIT is the outer one
    if m is None:
        body = f"{body} LIMIT {max_rows}"
    elif int(m.group(1)) > max_rows:
        body = body[:m.start(1)] + str(max_rows) + body[m.end(1):]
    return SQLVerdict(not problems, body, problems)


def readonly_connection(path: str) -> sqlite3.Connection:
    """SQLite opened read-only at the file level: even a validator bug cannot write."""
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def run_guarded(con: sqlite3.Connection, sql: str, allowed_tables: set[str], max_rows: int = 200) -> dict:
    v = check_sql(sql, allowed_tables, max_rows)
    if not v.ok:
        return {"ok": False, "problems": v.problems, "sql": sql}
    try:
        rows = [dict(r) for r in con.execute(v.sql).fetchall()]
    except sqlite3.Error as e:                     # give the error back to the LLM for one repair round
        return {"ok": False, "problems": [f"database error: {e}"], "sql": v.sql}
    return {"ok": True, "sql": v.sql, "rows": rows, "n": len(rows), "truncated": len(rows) >= max_rows}


def execution_match(con: sqlite3.Connection, pred_sql: str, gold_sql: str) -> bool:
    """Execution accuracy (as in Spider/BIRD): same result set, order-insensitive unless gold has ORDER BY."""
    try:
        p = [tuple(r) for r in con.execute(pred_sql).fetchall()]
    except sqlite3.Error:
        return False
    g = [tuple(r) for r in con.execute(gold_sql).fetchall()]
    return p == g if re.search(r"\border\s+by\b", gold_sql, re.I) else sorted(map(repr, p)) == sorted(map(repr, g))
