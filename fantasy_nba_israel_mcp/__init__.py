"""Fantasy NBA League MCP Server.

A Model Context Protocol server for accessing Fantasy NBA League statistics and rankings.
"""

from fantasy_nba_israel_mcp.server import mcp
from fantasy_nba_israel_mcp.core import (
    get_averages_league_rankings,
    get_teams,
    get_average_stats,
    get_team_details,
    get_league_shots_stats,
    query_team_scores_snapshots,
    get_snapshots,
)

__version__ = "0.4.0"
__all__ = [
    "mcp",
    "get_averages_league_rankings",
    "get_teams",
    "get_average_stats",
    "get_team_details",
    "get_league_shots_stats",
    "query_team_scores_snapshots",
    "get_snapshots",
]
