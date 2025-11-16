"""Main MCP server implementation for Fantasy NBA League.

This MCP server provides access to a rotisserie (roto) fantasy basketball league.
Teams compete in 8 statistical categories, earning ranking points based on their
performance relative to other teams.

API ENDPOINTS OVERVIEW:

1. getTeams() - Get list of all teams and their IDs
2. getAveragesLeagueRankings() - Get ranking points and overall standings (ROTO SCORING)
3. getAverageStats() - Get actual statistical performance (per-game averages)
4. getTeamDetails() - Get comprehensive team data (combines rankings, stats, and roster)
5. getLeagueShotsStats() - Get shooting statistics (FG/FT totals and percentages)

KEY CONCEPTS:

RANKING POINTS vs ACTUAL STATS:
- getAveragesLeagueRankings() returns RANKING POINTS (roto scoring: 1-N points per category)
- getAverageStats() returns ACTUAL PERFORMANCE (e.g., 25.3 assists per game)
- getTeamDetails() provides BOTH types of data

ROTISSERIE SCORING SYSTEM:
- Teams are ranked 1st to Nth in each of 8 categories
- Best team gets N points, second-best gets N-1, worst gets 1
- total_points = sum of points from all 8 categories
- Overall rank is determined by total_points (highest total = rank 1)

8 STATISTICAL CATEGORIES:
- FG% (Field Goal Percentage)
- FT% (Free Throw Percentage)
- 3PM (Three-Pointers Made)
- AST (Assists)
- REB (Rebounds)
- STL (Steals - חטיפות in Hebrew)
- BLK (Blocks)
- PTS (Points)
"""

from mcp.server.fastmcp import FastMCP
import httpx

mcp = FastMCP("fantasy-nba-israel-mcp")

BACKEND_API_URL = "https://fantasyaverageweb.onrender.com/api"

@mcp.tool()
def getAveragesLeagueRankings(order: str = "desc"):
    """
    Get the average league rankings from the API.
    
    IMPORTANT - SCORING SYSTEM EXPLANATION:
    This is a ROTISSERIE (ROTO) fantasy league. Teams earn ranking points in 8 categories.
    
    CRITICAL: Do NOT confuse "ranking points" with "rank position"!
    - Category values (fg_percentage, ast, reb, etc.) = POINTS earned (higher is better)
    - The "rank" field = actual position/place in standings (1 = first place)
    
    HOW RANKING POINTS WORK:
    - In each category, teams are ranked 1st to Nth (where N = number of teams)
    - Best team in a category gets N points, second-best gets N-1, worst gets 1
    - Example in 12-team league: 1st place = 12 pts, 2nd = 11 pts, ..., 12th = 1 pt
    - total_points = sum of points from all 8 categories
    - Overall "rank" is determined by total_points (highest total = rank 1)
    
    EXAMPLE in a 12-team league:
    {
        "team": {"team_name": "Best Team"},
        "ast": 12.0,           // Earned 12 pts (1st place in assists)
        "reb": 11.0,           // Earned 11 pts (2nd place in rebounds)
        "stl": 8.0,            // Earned 8 pts (5th place in steals)
        ...other categories...
        "total_points": 73.0,  // Sum of all 8 category points
        "rank": 1,             // Overall standing: 1st place
        "GP": 55               // Games played (informational only, not ranked)
    }
    
    Args:
        order: Sort order for rankings.
               - "desc" = best to worst (top teams first, "from top to bottom", "מלמעלה למטה")
               - "asc" = worst to best (bottom teams first, "from bottom to top", "מלמטה למעלה")
               Default is "desc".
    
    Returns:
        A list of teams with their rankings, total points, and stats per category.
        Each item in the list is a dictionary with the following keys: {
            "team": {
                "team_id": <team_id>,
                "team_name": <team_name>
            },
            "fg_percentage": <ranking_points_for_field_goal_percentage>,
            "ft_percentage": <ranking_points_for_free_throw_percentage>,
            "three_pm": <ranking_points_for_three_pointers_made>,
            "ast": <ranking_points_for_assists>,
            "reb": <ranking_points_for_rebounds>,
            "stl": <ranking_points_for_steals>,
            "blk": <ranking_points_for_blocks>,
            "pts": <ranking_points_for_points>,
            "total_points": <sum_of_all_category_ranking_points>,
            "rank": <overall_position_1_is_first_place>,
            "GP": <games_played_not_ranked>
        }
        
    NOTES:
    - Higher values in categories = better performance (more ranking points earned)
    - "rank" field is opposite: lower number = better (1 is first place)
    - GP (games played) is informational only, not used in scoring
    - When referring to steals in Hebrew, use חטיפות (not גניבות)
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
    Get the list of all teams in the fantasy league.
    
    Use this endpoint to discover team IDs for use with other endpoints like getTeamDetails().
    
    Returns:
        A list of teams with their team_id and team_name.
        Each item in the list is a dictionary with the following keys: {
            "team_id": <integer_team_identifier>,
            "team_name": <string_team_name>
        }
        
    NOTES:
    - Team IDs are required for getTeamDetails(team_id)
    - Team names may contain emojis or special characters
    - The list includes all active teams in the league
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
    Get the average statistics (actual performance numbers) for all teams from the API.
    
    IMPORTANT: This returns ACTUAL PERFORMANCE STATS, NOT ranking points!
    - This is different from getAveragesLeagueRankings() which returns ranking points
    - Use this endpoint to see actual per-game averages (e.g., 25.3 assists per game)
    - Use getAveragesLeagueRankings() to see rotisserie ranking points (e.g., 12 points earned)
    
    Args:
        use_normalized: If True, returns normalized data (0-1 scale) for comparison.
                       If False, returns raw statistical values (e.g., 45.6% FG, 12.3 AST).
                       Default is False.
    
    Returns:
        A list of teams with their actual statistical averages per game.
        Each item in the list is a dictionary with the following structure:
        {
            "team": {
                "team_id": <team_id>,
                "team_name": <team_name>
            },
            "stats": {
                "FG%": <field_goal_percentage_as_decimal>,
                "FT%": <free_throw_percentage_as_decimal>,
                "3PM": <three_pointers_made_per_game>,
                "AST": <assists_per_game>,
                "REB": <rebounds_per_game>,
                "STL": <steals_per_game>,
                "BLK": <blocks_per_game>,
                "PTS": <points_per_game>,
                "GP": <games_played>
            }
        }
        
    NOTES:
    - Percentages are decimals (0.456 = 45.6%)
    - All counting stats (3PM, AST, REB, STL, BLK, PTS) are per-game averages
    - When use_normalized=True, all values are scaled 0-1 for heatmap visualization
    - GP (games played) is a total count, not an average
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
    
    This endpoint combines multiple data types for a single team:
    1. Raw statistical averages (actual performance numbers)
    2. Ranking points (rotisserie scoring system)
    3. Category ranks (position in each category, 1=best)
    4. Player roster with individual stats
    
    IMPORTANT - Understanding the Data Sections:
    
    "raw_averages" = Actual statistical performance (e.g., 45.6% FG, 12.3 assists per game)
    "ranking_stats" = Rotisserie points earned in each category (see explanation below)
    "category_ranks" = Ordinal position in each category (1=1st place, 2=2nd place, etc.)
    "shot_chart" = Raw totals for field goals and free throws (not averages)
    
    RANKING STATS EXPLANATION (Same as getAveragesLeagueRankings):
    This is a ROTISSERIE (ROTO) fantasy league. Teams earn ranking points in 8 categories.
    
    CRITICAL: Do NOT confuse "ranking points" with "category ranks"!
    - ranking_stats values (e.g., ast: 12.0) = POINTS earned (higher is better)
    - category_ranks values (e.g., AST: 1) = position/place (lower is better, 1 = first)
    
    HOW RANKING POINTS WORK:
    - In each category, teams are ranked 1st to Nth (where N = number of teams)
    - Best team in a category gets N points, second-best gets N-1, worst gets 1
    - Example in 12-team league: 1st place = 12 pts, 2nd = 11 pts, ..., 12th = 1 pt
    - total_points = sum of points from all 8 categories
    - Overall "rank" is determined by total_points (highest total = rank 1)

    Args:
        team_id: The ID of the team to get details for. Use getTeams() to see all team IDs.

    Returns:
        A dictionary containing comprehensive team information: {
            "team": {
                "team_id": <team_id>,
                "team_name": <team_name>
            },
            "espn_url": <espn_team_page_url_string>,
            
            "shot_chart": {
                "team": {"team_id": <id>, "team_name": <name>},
                "fgm": <total_field_goals_made>,
                "fga": <total_field_goals_attempted>,
                "fg_percentage": <calculated_field_goal_percentage_as_decimal>,
                "ftm": <total_free_throws_made>,
                "fta": <total_free_throws_attempted>,
                "ft_percentage": <calculated_free_throw_percentage_as_decimal>,
                "gp": <games_played>
            },
            
            "raw_averages": {
                "fg_percentage": <average_field_goal_percentage_as_decimal>,
                "ft_percentage": <average_free_throw_percentage_as_decimal>,
                "three_pm": <average_three_pointers_made_per_game>,
                "ast": <average_assists_per_game>,
                "reb": <average_rebounds_per_game>,
                "stl": <average_steals_per_game>,
                "blk": <average_blocks_per_game>,
                "pts": <average_points_per_game>,
                "gp": <games_played>,
                "team": {"team_id": <id>, "team_name": <name>}
            },
            
            "ranking_stats": {
                "team": {"team_id": <id>, "team_name": <name>},
                "fg_percentage": <ranking_points_earned_in_fg_percentage>,
                "ft_percentage": <ranking_points_earned_in_ft_percentage>,
                "three_pm": <ranking_points_earned_in_three_pointers>,
                "ast": <ranking_points_earned_in_assists>,
                "reb": <ranking_points_earned_in_rebounds>,
                "stl": <ranking_points_earned_in_steals>,
                "blk": <ranking_points_earned_in_blocks>,
                "pts": <ranking_points_earned_in_points>,
                "gp": <games_played_not_ranked>,
                "total_points": <sum_of_all_8_category_ranking_points>,
                "rank": <overall_standing_1_is_first_place>
            },
            
            "category_ranks": {
                "FG%": <position_in_field_goal_percentage_1_is_best>,
                "FT%": <position_in_free_throw_percentage_1_is_best>,
                "3PM": <position_in_three_pointers_1_is_best>,
                "AST": <position_in_assists_1_is_best>,
                "REB": <position_in_rebounds_1_is_best>,
                "STL": <position_in_steals_1_is_best>,
                "BLK": <position_in_blocks_1_is_best>,
                "PTS": <position_in_points_1_is_best>
            },
            
            "players": [
                {
                    "player_name": <player_full_name_string>,
                    "pro_team": <nba_team_abbreviation_string>,
                    "positions": <list_of_eligible_positions>,
                    "stats": {
                        "pts": <average_points_per_game>,
                        "reb": <average_rebounds_per_game>,
                        "ast": <average_assists_per_game>,
                        "stl": <average_steals_per_game>,
                        "blk": <average_blocks_per_game>,
                        "fgm": <average_field_goals_made_per_game>,
                        "fga": <average_field_goals_attempted_per_game>,
                        "ftm": <average_free_throws_made_per_game>,
                        "fta": <average_free_throws_attempted_per_game>,
                        "fg_percentage": <field_goal_percentage_as_decimal>,
                        "ft_percentage": <free_throw_percentage_as_decimal>,
                        "three_pm": <average_three_pointers_made_per_game>,
                        "minutes": <average_minutes_per_game>,
                        "gp": <total_games_played>
                    },
                    "team_id": <fantasy_team_id>
                }
            ]
        }
        
    EXAMPLE - Understanding the Different Data Types:
    If a team shows:
    - raw_averages.ast: 25.3 → Team averages 25.3 assists per game (actual performance)
    - ranking_stats.ast: 12.0 → Team earned 12 ranking points in assists (1st place in 12-team league)
    - category_ranks.AST: 1 → Team is ranked 1st in assists category
    
    NOTES:
    - Higher ranking_stats values = more points earned = better
    - Lower category_ranks values = better position (1 is first place)
    - raw_averages are the actual statistical performance
    - GP (games played) is informational only, not used in ranking calculations
    - When referring to steals in Hebrew, use חטיפות (not גניבות)
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

# @mcp.tool()
# def getAllPlayers(page: int = 1, limit: int = 500):
#     """
#     Get all players from the API with pagination support.
    
#     This endpoint returns ALL players in the fantasy league including:
#     - Players currently on fantasy teams (status: "ONTEAM")
#     - Free agents available for pickup (status: "FREEAGENT")  
#     - Players on waivers (status: "WAIVERS")
    
#     Args:
#         page: The page number to retrieve. Use this to paginate through large player lists.
#               Default is 1 (first page). Minimum value is 1.
#         limit: Number of players to return per page. This controls how many players
#                you get in a single request. Default is 500 (maximum allowed).
#                Valid range: 10-500 players per page.
    
#     Returns:
#         A paginated response object containing player data and pagination metadata.
#         The response is a dictionary with the following structure: {
#             "players": [
#                 {
#                     "player_name": <string, e.g., "LeBron James">,
#                     "pro_team": <string, NBA team abbreviation, e.g., "LAL">,
#                     "positions": <list of strings, e.g., ["SF", "PF"]>,
#                     "stats": {
#                         "pts": <int, total points>,
#                         "reb": <int, total rebounds>,
#                         "ast": <int, total assists>,
#                         "stl": <int, total steals>,
#                         "blk": <int, total blocks>,
#                         "fgm": <int, total field goals made>,
#                         "fga": <int, total field goals attempted>,
#                         "ftm": <int, total free throws made>,
#                         "fta": <int, total free throws attempted>,
#                         "fg_percentage": <float, field goal percentage as decimal (e.g., 0.456 = 45.6%)>,
#                         "ft_percentage": <float, free throw percentage as decimal (e.g., 0.850 = 85.0%)>,
#                         "three_pm": <int, total three-pointers made>,
#                         "minutes": <int, total minutes played>,
#                         "gp": <int, total games played>
#                     },
#                     "team_id": <int, fantasy team ID (0 if not on a team)>,
#                     "status": <string, one of: "ONTEAM", "FREEAGENT", "WAIVERS">
#                 }
#             ],
#             "total_count": <int, total number of players across all pages>,
#             "page": <int, current page number>,
#             "limit": <int, players per page in this response>,
#             "has_more": <boolean, true if there are more pages available>
#         }
    
#     Example Usage:
#         - Get first 500 players: getAllPlayers()
#         - Get next 500 players: getAllPlayers(page=2)
#         - Get 100 players at a time: getAllPlayers(limit=100)
#         - Get second page with 100 per page: getAllPlayers(page=2, limit=100)
    
#     Notes:
#         - Use the "status" field to filter between rostered players, free agents, and waivers
#         - Use "has_more" to determine if you need to fetch additional pages
#         - "total_count" tells you the total number of players available
#         - All stats are averaged per game except "gp" which is total games played
#     """
#     try:
#         response = httpx.get(
#             f"{BACKEND_API_URL}/players/",
#             params={"page": page, "limit": limit},
#             timeout=10
#         )
#         return response.json()
#     except httpx.HTTPStatusError as e:
#         return {"error": f"HTTP status error: {e.response.status_code} {e.response.text}"}
#     except httpx.TimeoutException as e:
#         return {"error": "Request timed out. The backend server may be slow or unavailable."}
#     except Exception as e:
#         return {"error": f"An unexpected error occurred: {e.__class__.__name__}: {str(e)}"}

@mcp.tool()
def getLeagueShotsStats():
    """
    Get league-wide shooting statistics (field goals and free throws) for all teams.
    
    This endpoint provides CUMULATIVE TOTALS (not per-game averages) for shooting stats.
    Useful for understanding overall team shooting efficiency across the season.

    Returns:
        A dictionary containing league-wide shooting statistics: {
            "shots": [
                {
                    "team": {
                        "team_id": <team_id>,
                        "team_name": <team_name>
                    },
                    "fgm": <total_field_goals_made>,
                    "fga": <total_field_goals_attempted>,
                    "fg_percentage": <calculated_field_goal_percentage_as_decimal>,
                    "ftm": <total_free_throws_made>,
                    "fta": <total_free_throws_attempted>,
                    "ft_percentage": <calculated_free_throw_percentage_as_decimal>,
                    "gp": <games_played>
                }
            ]
        }

    NOTES:
    - fgm, fga, ftm, fta are TOTALS across all games, not per-game averages
    - fg_percentage and ft_percentage are calculated from totals (fgm/fga, ftm/fta)
    - Percentages are returned as decimals (e.g., 0.456 = 45.6%)
    - The list contains one entry per team with their complete shooting profile
    """
    try:
        response = httpx.get(f"{BACKEND_API_URL}/league/shots", timeout=10)
        return response.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP status error: {e.response.status_code} {e.response.text}"}
    except httpx.TimeoutException as e:
        return {"error": "Request timed out. The backend server may be slow or unavailable."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e.__class__.__name__}: {str(e)}"}