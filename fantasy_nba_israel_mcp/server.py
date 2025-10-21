"""Main MCP server implementation for Fantasy NBA League."""

from mcp.server.fastmcp import FastMCP
import httpx

mcp = FastMCP("fantasy-nba-israel-mcp")

BACKEND_API_URL = "https://fantasyaverageweb.onrender.com/api"

@mcp.tool()
def getAveragesLeagueRankings(order: str = "desc"):
    """
    Get the average league rankings from the API.
    Args:
        order: Sort order for rankings.
               - "desc" = best to worst (top teams first, "from top to bottom", "מלמעלה למטה")
               - "asc" = worst to best (bottom teams first, "from bottom to top", "מלמטה למעלה")
               Default is "desc".
    
    Returns:
        A list of teams with their rankings, total points, and stats per category.
        each item in the list is a dictionary with the following keys: {
            "team": {
                "team_id": <team_id>,
                "team_name": <team_name>
            },
            "fg_percentage": <fg_percentage>,
            "ft_percentage": <ft_percentage>,
            "three_pm": <three_pm>,
            "ast": <ast>,
            "reb": <reb>,
            "stl": <stl>,
            "blk": <blk>,
            "pts": <pts>,
            "total_points": <total_points>,
            "rank": <rank>
            }"
    """
    try:
        response = httpx.get(f"{BACKEND_API_URL}/rankings?order={order}", timeout=10)
        return response.json()['rankings']
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP status error: {e.response.status_code} {e.response.text}"}
    except httpx.TimeoutException as e:
        return {"error": "Request timed out. The backend server may be slow or unavailable."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e.__class__.__name__}: {str(e)}"}

@mcp.tool()
def getTeams():
    """
    Get the list of teams from the API.
    Returns:
        A list of teams with their team_id and team_name.
        each item in the list is a dictionary with the following keys: {
            "team_id": <team_id>,
            "team_name": <team_name>
        }
    """
    try:
        response = httpx.get(f"{BACKEND_API_URL}/teams/", timeout=10)
        return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP status error: {e.response.status_code} {e.response.text}"}
    except httpx.TimeoutException as e:
        return {"error": "Request timed out. The backend server may be slow or unavailable."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e.__class__.__name__}: {str(e)}"}

@mcp.tool()
def getAverageStats(use_normalized: bool = False):
    """
    Get the average stats from the API in a user-friendly format.
    
    Args:
        use_normalized: If True, returns normalized data (0-1 scale). 
                       If False, returns raw stat values. Default is False.
    
    Returns:
        A list of teams with their stats mapped by category name.
        Each item in the list is a dictionary with the following structure:
        {
            "team": {
                "team_id": <team_id>,
                "team_name": <team_name>
            },
            "stats": {
                "FG%": <value>,
                "FT%": <value>,
                "3PM": <value>,
                "AST": <value>,
                "REB": <value>,
                "STL": <value>,
                "BLK": <value>,
                "PTS": <value>
            }
        }
    """
    try:
        response = httpx.get(f"{BACKEND_API_URL}/analytics/heatmap", timeout=10)
        response_data = response.json()
        
        categories = response_data['categories']
        teams = response_data['teams']
        data = response_data['normalized_data'] if use_normalized else response_data['data']
        
        # Transform data into user-friendly format
        result = []
        for team_index, team in enumerate(teams):
            team_stats = {
                "team": {
                    "team_id": team["team_id"],
                    "team_name": team["team_name"]
                },
                "stats": {}
            }
            
            # Map each category to its corresponding value
            for category_index, category_name in enumerate(categories):
                team_stats["stats"][category_name] = data[team_index][category_index]
            
            result.append(team_stats)
        
        return result
        
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP status error: {e.response.status_code} {e.response.text}"}
    except httpx.TimeoutException as e:
        return {"error": "Request timed out. The backend server may be slow or unavailable."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e.__class__.__name__}: {str(e)}"}

@mcp.tool()
def getTeamPlayers(team_id: int):
    """
    Get the list of players for a team from the API.
    Args:
        team_id: The ID of the team to get the players for.
    Returns:
        A list of players for the team.
        
        each item in the list is a dictionary with the following keys: {
            "player_name": <player_name>,
            "pro_team": <pro_team>,
            "positions": <positions>,
            "stats": {
                "pts": <pts>,
                "reb": <reb>,
                "ast": <ast>,
                "stl": <stl>,
                "blk": <blk>,
                "fgm": <fgm>,
                "fga": <fga>,
                "ftm": <ftm>,
                "fta": <fta>
                "fg_percentage": <fg_percentage>,
                "ft_percentage": <ft_percentage>,
                "three_pm": <three_pm>,
                "gp": <gp>
            }
        }
    """
    try:
        response = httpx.get(f"{BACKEND_API_URL}/teams/{team_id}/players", timeout=10)
        return response.json()["players"]
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP status error: {e.response.status_code} {e.response.text}"}
    except httpx.TimeoutException as e:
        return {"error": "Request timed out. The backend server may be slow or unavailable."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e.__class__.__name__}: {str(e)}"}

@mcp.tool()
def getAllPlayers():
    """
    Get the list of all players from the API.
    Returns:
        A list of all players.
        each item in the list is a dictionary with the following keys: {
            "player_name": <player_name>,
            "pro_team": <pro_team>,
            "positions": <positions>,
            "stats": {
                "pts": <pts>,
                "reb": <reb>,
                "ast": <ast>,
                "stl": <stl>,
                "blk": <blk>,
                "fgm": <fgm>,
                "fga": <fga>,
                "ftm": <ftm>,
                "fta": <fta>
                "fg_percentage": <fg_percentage>,
                "ft_percentage": <ft_percentage>,
                "three_pm": <three_pm>,
                "gp": <gp>
            },
            "team_id": <team_id>,
        }
    """
    try:
        response = httpx.get(f"{BACKEND_API_URL}/players/", timeout=10)
        return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP status error: {e.response.status_code} {e.response.text}"}
    except httpx.TimeoutException as e:
        return {"error": "Request timed out. The backend server may be slow or unavailable."}