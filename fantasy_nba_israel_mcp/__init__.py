"""Fantasy NBA League MCP Server.

A Model Context Protocol server for accessing Fantasy NBA League statistics and rankings.
"""

from fantasy_nba_israel_mcp.server import (
    mcp,
    getAveragesLeagueRankings,
    getTeams,
    getAverageStats,
    getTeamPlayers,
    getAllPlayers
)

__version__ = "0.1.0"
__all__ = [
    "mcp", 
    "getAveragesLeagueRankings", 
    "getTeams", 
    "getAverageStats", 
    "getTeamPlayers",
    "getAllPlayers"
]

