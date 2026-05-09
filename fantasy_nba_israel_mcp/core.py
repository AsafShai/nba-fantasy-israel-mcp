"""Core business logic for Fantasy NBA League — shared by MCP server and CLI."""

import os
import re
from typing import Optional

import httpx
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

BACKEND_API_URL = "https://fantasyaverageweb.onrender.com/api"
DATABASE_URL = os.environ.get("FANTASY_DB_URL", "")

_db_connection = None

VALID_SNAPSHOT_STATS = frozenset({
    "gp", "fgm", "fga", "fg_pct", "ftm", "fta", "ft_pct",
    "three_pm", "reb", "ast", "stl", "blk", "pts",
})


def get_db_connection():
    """Lazy connection with auto-reconnect. Creates on first use, reuses after."""
    global _db_connection
    try:
        if _db_connection is not None and not _db_connection.closed:
            _db_connection.isolation_level
            return _db_connection
    except Exception:
        try:
            _db_connection.close()
        except Exception:
            pass
        _db_connection = None

    _db_connection = psycopg2.connect(DATABASE_URL)
    _db_connection.autocommit = True
    return _db_connection


def get_averages_league_rankings(order: str = "desc"):
    try:
        response = httpx.get(f"{BACKEND_API_URL}/rankings?order={order}", timeout=10)
        return response.json()['rankings']
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP status error: {e.response.status_code} {e.response.text}"}
    except httpx.TimeoutException:
        return {"error": "Request timed out. The backend server may be slow or unavailable."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e.__class__.__name__}: {str(e)}"}


def get_teams():
    try:
        response = httpx.get(f"{BACKEND_API_URL}/teams/", timeout=10)
        return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP status error: {e.response.status_code} {e.response.text}"}
    except httpx.TimeoutException:
        return {"error": "Request timed out. The backend server may be slow or unavailable."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e.__class__.__name__}: {str(e)}"}


def get_average_stats(use_normalized: bool = False):
    try:
        response = httpx.get(f"{BACKEND_API_URL}/analytics/heatmap", timeout=10)
        response_data = response.json()

        categories = response_data['categories']
        teams = response_data['teams']
        data = response_data['normalized_data'] if use_normalized else response_data['data']

        result = []
        for team_index, team in enumerate(teams):
            team_stats = {
                "team": {
                    "team_id": team["team_id"],
                    "team_name": team["team_name"]
                },
                "stats": {}
            }
            for category_index, category_name in enumerate(categories):
                team_stats["stats"][category_name] = data[team_index][category_index]
            result.append(team_stats)

        return result

    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP status error: {e.response.status_code} {e.response.text}"}
    except httpx.TimeoutException:
        return {"error": "Request timed out. The backend server may be slow or unavailable."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e.__class__.__name__}: {str(e)}"}


def get_team_details(team_id: int):
    try:
        response = httpx.get(f"{BACKEND_API_URL}/teams/{team_id}", timeout=10)
        return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP status error: {e.response.status_code} {e.response.text}"}
    except httpx.TimeoutException:
        return {"error": "Request timed out. The backend server may be slow or unavailable."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e.__class__.__name__}: {str(e)}"}


def get_league_shots_stats():
    try:
        response = httpx.get(f"{BACKEND_API_URL}/league/shots", timeout=10)
        return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP status error: {e.response.status_code} {e.response.text}"}
    except httpx.TimeoutException:
        return {"error": "Request timed out. The backend server may be slow or unavailable."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e.__class__.__name__}: {str(e)}"}


def query_team_scores_snapshots(query: str):
    """Execute a read-only SELECT query against team_daily_snapshot. Used internally by the MCP tool."""
    sanitized = query.strip().rstrip(";").strip()

    if not re.match(r"(?i)^SELECT\s", sanitized):
        return {"error": "Only SELECT queries are allowed. INSERT, UPDATE, DELETE, DROP, etc. are rejected."}

    forbidden = re.compile(
        r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|EXEC|EXECUTE|INTO\s+OUTFILE|COPY)\b",
        re.IGNORECASE,
    )
    if forbidden.search(sanitized):
        return {"error": "Query contains forbidden keywords. Only pure SELECT/read queries are allowed."}

    return _run_db_query(sanitized, [])


def get_snapshots(
    date: Optional[str] = None,
    team_id: Optional[int] = None,
    stat: Optional[str] = None,
    limit: int = 10,
):
    """Query team_daily_snapshot with pre-built filters. Table schema stays internal."""
    if stat is not None and stat not in VALID_SNAPSHOT_STATS:
        return {"error": f"Invalid stat '{stat}'. Valid options: {', '.join(sorted(VALID_SNAPSHOT_STATS))}"}

    conditions = []
    params: list = []

    if date is not None:
        conditions.append("date = %s")
        params.append(date)
    if team_id is not None:
        conditions.append("team_id = %s")
        params.append(team_id)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    # stat is validated against VALID_SNAPSHOT_STATS above — safe to interpolate as identifier
    order_clause = f"ORDER BY {stat} DESC" if stat else "ORDER BY date DESC, team_name ASC"
    params.append(limit)

    sql = f"SELECT * FROM team_daily_snapshot {where_clause} {order_clause} LIMIT %s"
    return _run_db_query(sql, params)


def _run_db_query(sql: str, params: list):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description] if cur.description else []
        cur.close()

        serialized_rows = []
        for row in rows:
            serialized_row = {}
            for key, value in row.items():
                if hasattr(value, "isoformat"):
                    serialized_row[key] = value.isoformat()
                elif isinstance(value, (int, float, str, bool, type(None))):
                    serialized_row[key] = value
                else:
                    serialized_row[key] = str(value)
            serialized_rows.append(serialized_row)

        return {
            "columns": columns,
            "rows": serialized_rows,
            "row_count": len(serialized_rows),
        }

    except psycopg2.Error as e:
        return {"error": f"Database error: {str(e).strip()}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e.__class__.__name__}: {str(e)}"}
