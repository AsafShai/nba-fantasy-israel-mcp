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
            "GP": <GP>,
            }"
        in each statistical category (except for total points and rank), the higher thee value is, the better the team is.
        for example, for 12 teams league, the best team in assists has 12, the next 11 and so on.
        total points is the sum of the points in all categories, so the best team in total points has the most points.
        rank is the rank of the team in the league, the best team has rank 1, the next 2 and so on.
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
                "PTS": <value>,
                "GP": <value>,
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
def getTeamDetails(team_id: int):
    """
    Get comprehensive details for a specific team from the API.

    Args:
        team_id: The ID of the team to get details for.

    Returns:
        A dictionary containing comprehensive team information: {
            "team": {
                "team_id": <team_id>,
                "team_name": <team_name>
            },
            "espn_url": <espn_team_page_url>,
            "shot_chart": {
                "team": {"team_id": <id>, "team_name": <name>},
                "fgm": <field_goals_made>,
                "fga": <field_goals_attempted>,
                "fg_percentage": <field_goal_percentage>,
                "ftm": <free_throws_made>,
                "fta": <free_throws_attempted>,
                "ft_percentage": <free_throw_percentage>,
                "gp": <games_played>
            },
            "raw_averages": {
                "fg_percentage": <avg_fg_percentage>,
                "ft_percentage": <avg_ft_percentage>,
                "three_pm": <avg_three_pointers_made>,
                "ast": <avg_assists>,
                "reb": <avg_rebounds>,
                "stl": <avg_steals>,
                "blk": <avg_blocks>,
                "pts": <avg_points>,
                "gp": <games_played>,
                "team": {"team_id": <id>, "team_name": <name>}
            },
            "ranking_stats": {
                "team": {"team_id": <id>, "team_name": <name>},
                "fg_percentage": <rank_points>,
                "ft_percentage": <rank_points>,
                "three_pm": <rank_points>,
                "ast": <rank_points>,
                "reb": <rank_points>,
                "stl": <rank_points>,
                "blk": <rank_points>,
                "pts": <rank_points>,
                "gp": <games_played>,
                "total_points": <total_rank_points>,
                "rank": <overall_rank>
            },
            "category_ranks": {
                "FG%": <rank_in_category>,
                "FT%": <rank_in_category>,
                "3PM": <rank_in_category>,
                "AST": <rank_in_category>,
                "REB": <rank_in_category>,
                "STL": <rank_in_category>,
                "BLK": <rank_in_category>,
                "PTS": <rank_in_category>
            },
            "players": [
                {
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
                        "fta": <fta>,
                        "fg_percentage": <fg_percentage>,
                        "ft_percentage": <ft_percentage>,
                        "three_pm": <three_pm>,
                        "minutes": <minutes>,
                        "gp": <gp>
                    },
                    "team_id": <team_id>
                }
            ]
        }
        for the ranking stats:
        in each statistical category (except for total points and rank), the higher thee value is, the better the team is.
        for example, for 12 teams league, the best team in assists has 12, the next 11 and so on.
        total points is the sum of the points in all categories, so the best team in total points has the most points.
        rank is the rank of the team in the league, the best team has rank 1, the next 2 and so on.
        also gp is not ranked, it is the total games played by the team.
    """
    try:
        response = httpx.get(f"{BACKEND_API_URL}/teams/{team_id}", timeout=10)
        return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP status error: {e.response.status_code} {e.response.text}"}
    except httpx.TimeoutException as e:
        return {"error": "Request timed out. The backend server may be slow or unavailable."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e.__class__.__name__}: {str(e)}"}

@mcp.tool()
def getAllPlayers(page: int = 1, limit: int = 500):
    """
    Get all players from the API with pagination support.
    
    This endpoint returns ALL players in the fantasy league including:
    - Players currently on fantasy teams (status: "ONTEAM")
    - Free agents available for pickup (status: "FREEAGENT")  
    - Players on waivers (status: "WAIVERS")
    
    Args:
        page: The page number to retrieve. Use this to paginate through large player lists.
              Default is 1 (first page). Minimum value is 1.
        limit: Number of players to return per page. This controls how many players
               you get in a single request. Default is 500 (maximum allowed).
               Valid range: 10-500 players per page.
    
    Returns:
        A paginated response object containing player data and pagination metadata.
        The response is a dictionary with the following structure: {
            "players": [
                {
                    "player_name": <string, e.g., "LeBron James">,
                    "pro_team": <string, NBA team abbreviation, e.g., "LAL">,
                    "positions": <list of strings, e.g., ["SF", "PF"]>,
                    "stats": {
                        "pts": <int, total points>,
                        "reb": <int, total rebounds>,
                        "ast": <int, total assists>,
                        "stl": <int, total steals>,
                        "blk": <int, total blocks>,
                        "fgm": <int, total field goals made>,
                        "fga": <int, total field goals attempted>,
                        "ftm": <int, total free throws made>,
                        "fta": <int, total free throws attempted>,
                        "fg_percentage": <float, field goal percentage as decimal (e.g., 0.456 = 45.6%)>,
                        "ft_percentage": <float, free throw percentage as decimal (e.g., 0.850 = 85.0%)>,
                        "three_pm": <int, total three-pointers made>,
                        "minutes": <int, total minutes played>,
                        "gp": <int, total games played>
                    },
                    "team_id": <int, fantasy team ID (0 if not on a team)>,
                    "status": <string, one of: "ONTEAM", "FREEAGENT", "WAIVERS">
                }
            ],
            "total_count": <int, total number of players across all pages>,
            "page": <int, current page number>,
            "limit": <int, players per page in this response>,
            "has_more": <boolean, true if there are more pages available>
        }
    
    Example Usage:
        - Get first 500 players: getAllPlayers()
        - Get next 500 players: getAllPlayers(page=2)
        - Get 100 players at a time: getAllPlayers(limit=100)
        - Get second page with 100 per page: getAllPlayers(page=2, limit=100)
    
    Notes:
        - Use the "status" field to filter between rostered players, free agents, and waivers
        - Use "has_more" to determine if you need to fetch additional pages
        - "total_count" tells you the total number of players available
        - All stats are averaged per game except "gp" which is total games played
    """
    try:
        response = httpx.get(
            f"{BACKEND_API_URL}/players/",
            params={"page": page, "limit": limit},
            timeout=10
        )
        return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP status error: {e.response.status_code} {e.response.text}"}
    except httpx.TimeoutException as e:
        return {"error": "Request timed out. The backend server may be slow or unavailable."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e.__class__.__name__}: {str(e)}"}

@mcp.tool()
def getLeagueShotsStats():
    """
    Get league-wide shooting statistics for all teams.

    Returns:
        A dictionary containing league-wide shooting statistics: {
            "shots": [
                {
                    "team": {
                        "team_id": <team_id>,
                        "team_name": <team_name>
                    },
                    "fgm": <field_goals_made>,
                    "fga": <field_goals_attempted>,
                    "fg_percentage": <field_goal_percentage>,
                    "ftm": <free_throws_made>,
                    "fta": <free_throws_attempted>,
                    "ft_percentage": <free_throw_percentage>,
                    "gp": <games_played>
                }
            ]
        }

        The list contains one entry per team with their shooting statistics.
        Percentages are returned as decimals (e.g., 0.456 = 45.6%).
    """
    try:
        response = httpx.get(f"{BACKEND_API_URL}/league/shots", timeout=10)
        return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP status error: {e.response.status_code} {e.response.text}"}
    except httpx.TimeoutException as e:
        return {"error": "Request timed out. The backend server may be slow or unavailable."}