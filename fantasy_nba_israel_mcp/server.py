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
import os
import re
import psycopg2
import psycopg2.extras
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("fantasy-nba-israel-mcp")

BACKEND_API_URL = "https://fantasyaverageweb.onrender.com/api"

DATABASE_URL = os.environ.get("FANTASY_DB_URL", "")

_db_connection = None


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
    - If you refer to comparing teams, distinguish between rank and total points, so f.e someone can be 1st place 70 total points and another team can be 2nd place 69 total points.
    - In that case, the difference is 2 points, not 1 place.
    """
    try:
        response = httpx.get(f"{BACKEND_API_URL}/rankings?order={order}", timeout=10)
        return response.json()['rankings']
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP status error: {e.response.status_code} {e.response.text}"}
    except httpx.TimeoutException:
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
    except httpx.TimeoutException:
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
    except httpx.TimeoutException:
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
                "FG%": <ranking_points_earned_in_fg_percentage>,
                "FT%": <ranking_points_earned_in_ft_percentage>,
                "3PM": <ranking_points_earned_in_three_pointers>,
                "AST": <ranking_points_earned_in_assists>,
                "REB": <ranking_points_earned_in_rebounds>,
                "STL": <ranking_points_earned_in_steals>,
                "BLK": <ranking_points_earned_in_blocks>,
                "PTS": <ranking_points_earned_in_points>
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
    except httpx.TimeoutException:
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
    except httpx.TimeoutException:
        return {"error": "Request timed out. The backend server may be slow or unavailable."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e.__class__.__name__}: {str(e)}"}


@mcp.tool()
def query_team_scores_snapshots(query: str):
    """
    Execute a READ-ONLY SQL query against the team_daily_snapshot table in PostgreSQL.

    This is the historical database — it stores CUMULATIVE SEASON TOTALS for every team
    as of each date. Each row is a complete snapshot: "here is where this team stands
    on this date". The table goes back to the start of the season (Oct 22, 2025).

    ONLY SELECT queries are allowed. INSERT, UPDATE, DELETE, DROP, etc. will be rejected.

    ==========================================================================
    TABLE: team_daily_snapshot
    ==========================================================================

    Each row = one team's cumulative season totals through a specific date.

    COLUMNS:
    -------------------------------------------------------------------------
    IDENTITY:
      id                  INT          - Auto-increment primary key
      scoring_period_id   INT          - ESPN scoring period number (sequential day
                                         number in the NBA season: 1, 2, 3...).
                                         Maps 1:1 with date. Period 1 = Oct 22, 2025.
      date                DATE         - Calendar date of this snapshot (e.g. 2026-03-05)
      team_id             INT          - ESPN fantasy team ID (use getTeams() for mapping)
      team_name           VARCHAR      - Team name (e.g. "50 Shades of Shai")

    CUMULATIVE SEASON TOTALS (through this date):
      gp                  INT          - Total games played by all players on this team
                                         through this date (sum of player-games)
      fgm                 INT          - Season total field goals MADE
      fga                 INT          - Season total field goals ATTEMPTED
      fg_pct              DECIMAL(6,4) - Season field goal %: fgm / fga (e.g. 0.4932)
      ftm                 INT          - Season total free throws MADE
      fta                 INT          - Season total free throws ATTEMPTED
      ft_pct              DECIMAL(6,4) - Season free throw %: ftm / fta (e.g. 0.8082)
      three_pm            INT          - Season total three-pointers made
      reb                 INT          - Season total rebounds
      ast                 INT          - Season total assists
      stl                 INT          - Season total steals
      blk                 INT          - Season total blocks
      pts                 INT          - Season total points

    METADATA:
      created_at          TIMESTAMP    - When this row was inserted

    UNIQUE KEYS:
      (scoring_period_id, team_id) — one snapshot per team per scoring period
      (date, team_id)              — one snapshot per team per date

    INDEXES: id, scoring_period_id, date, team_id
    -------------------------------------------------------------------------

    IMPORTANT QUERY PATTERNS:

    1. GET TOTALS AT A DATE (each row IS the totals):
       SELECT team_name, gp, pts, reb, ast FROM team_daily_snapshot
       WHERE date = '2026-03-05' ORDER BY pts DESC;

    2. GET WHAT HAPPENED BETWEEN TWO DATES (subtract snapshots):
       SELECT a.team_name, a.pts - b.pts AS period_pts, a.reb - b.reb AS period_reb
       FROM team_daily_snapshot a
       JOIN team_daily_snapshot b ON a.team_id = b.team_id
       WHERE a.date = '2026-03-05' AND b.date = '2026-03-01';

    3. GET AVERAGES AT A DATE (divide totals by gp):
       SELECT team_name, pts * 1.0 / gp AS avg_pts, reb * 1.0 / gp AS avg_reb
       FROM team_daily_snapshot WHERE date = '2026-03-05';

    4. GET PERIOD AVERAGES (diff then divide):
       SELECT a.team_name,
              (a.pts - b.pts) * 1.0 / NULLIF(a.gp - b.gp, 0) AS avg_pts_march
       FROM team_daily_snapshot a
       JOIN team_daily_snapshot b ON a.team_id = b.team_id
       WHERE a.date = '2026-03-05' AND b.date = '2026-03-01';

    5. TREND OVER TIME (multiple snapshots):
       SELECT date, pts, reb FROM team_daily_snapshot
       WHERE team_id = 8 AND date >= '2026-02-01' ORDER BY date;

    6. RANK TEAMS AT A DATE:
       SELECT team_name, pts,
              RANK() OVER (ORDER BY pts DESC) AS pts_rank
       FROM team_daily_snapshot WHERE date = '2026-03-05';

    7. LATEST AVAILABLE SNAPSHOT:
       SELECT * FROM team_daily_snapshot
       WHERE date = (SELECT MAX(date) FROM team_daily_snapshot)
       ORDER BY pts DESC;

    TIPS FOR THE AGENT:
    - Each row is CUMULATIVE (season totals through that date), not a single-day stat.
    - To get a single day or period, SUBTRACT two snapshots (newer - older).
    - For percentages over a period, use raw makes/attempts:
      (a.fgm - b.fgm) / NULLIF(a.fga - b.fga, 0) — NOT averaging fg_pct values.
    - gp = total player-games (if a team has 10 players who each played 60 games = 600 gp).
    - The table has 12 teams and ~137+ scoring periods, growing daily.
    - Use LIMIT to avoid returning too many rows when exploring.
    - Prefer specific date filters over full table scans.

    Args:
        query: A SQL SELECT statement to execute against the database.
               MUST be a SELECT query. All other statements are rejected.
               The query runs against the 'team_daily_snapshot' table.

    Returns:
        A dictionary with:
        - "columns": list of column names in the result
        - "rows": list of rows, each row is a dict mapping column name to value
        - "row_count": number of rows returned
        Or on error:
        - "error": description of what went wrong
    """
    sanitized = query.strip().rstrip(";").strip()

    if not re.match(r"(?i)^SELECT\s", sanitized):
        return {"error": "Only SELECT queries are allowed. INSERT, UPDATE, DELETE, DROP, etc. are rejected."}

    forbidden = re.compile(
        r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE|EXEC|EXECUTE|INTO\s+OUTFILE|COPY)\b",
        re.IGNORECASE,
    )
    if forbidden.search(sanitized):
        return {"error": "Query contains forbidden keywords. Only pure SELECT/read queries are allowed."}

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sanitized)
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


def _build_players_df() -> pd.DataFrame:
    """Fetch all players from the API and return a flat DataFrame."""
    response = httpx.get(
        f"{BACKEND_API_URL}/players/",
        params={"page": 1, "limit": 500},
        timeout=15,
    )
    response.raise_for_status()
    players = response.json()["players"]

    df = pd.json_normalize(players, sep=".")
    df.columns = [col.replace("stats.", "") for col in df.columns]
    df["positions"] = df["positions"].astype(str)
    return df


@mcp.tool()
def describePlayersDF():
    """
    Get statistical summary (describe) of all ~500 players in the league.

    Call this BEFORE filterPlayers to understand the data distribution —
    min, max, mean, std, quartiles for every numeric column, plus unique
    counts for categorical columns.  Use the output to build smart, precise
    filter expressions instead of loading the full player list.

    AVAILABLE COLUMNS (use these names in filterPlayers):
    -------------------------------------------------------
    Identifiers / categorical:
      player_name        str   Full name (e.g. "LeBron James")
      pro_team           str   NBA team abbreviation (e.g. "LAL")
      positions          str   Stringified list (e.g. "['PG', 'SG']")
      team_id            int   Fantasy team ID — 0 means no fantasy team
      status             str   "ONTEAM" | "FREEAGENT" | "WAIVERS"
      injured            bool  True if player is currently injured
      fantasy_team_name  str   Name of the owning fantasy team ("" if no team)

    Ratings (overall composite score, higher = better):
      season_rating  float  Full-season composite rating
      last7_rating   float  Rating over the last 7 days
      last15_rating  float  Rating over the last 15 days
      last30_rating  float  Rating over the last 30 days

    Season TOTALS (divide by gp to get per-game):
      pts           float  Total points scored
      reb           float  Total rebounds
      ast           float  Total assists
      stl           float  Total steals
      blk           float  Total blocks
      three_pm      float  Total three-pointers made
      fgm           float  Total field goals made
      fga           float  Total field goals attempted
      ftm           float  Total free throws made
      fta           float  Total free throws attempted
      minutes       float  Total minutes played

    Percentages (already computed):
      fg_percentage float  Field-goal % as decimal (e.g. 0.551)
      ft_percentage float  Free-throw % as decimal (e.g. 0.891)

    Count:
      gp            int    Total games played

    HOW TO INTERPRET FOR TRADE ANALYSIS:
    -------------------------------------------------------
    - season_rating NaN count: the "count" row in describe shows how many players
      have a valid rating. Players missing a rating must be excluded from all trade
      comparisons — they have too little data to judge value fairly.
    - season_rating mean (~5-8 typical): players above the 75th percentile are
      elite trade assets; below 25th percentile are low-value.
    - last30_rating vs season_rating: if last30 >> season, the player is trending
      up (buy-high target). If last30 << season, they may be slumping (sell-high).
    - gp: players with gp < 20 have unreliable stats — always flag in proposals.
    - fg_percentage / ft_percentage: use the 25th/75th percentile values from
      describe as your "weak" / "strong" shooting thresholds per category.
    - Use the 75th percentile of pts/reb/ast/stl/blk as the "league strong"
      benchmark when evaluating category contributions.
    - injured: the describe "freq" row on the injured column shows how many
      players are currently out — useful context before trade season.

    Returns:
        dict — result of df.describe(include='all').to_dict(), keyed by column name.
    """
    try:
        df = _build_players_df()
        return df.describe(include="all").to_dict()
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP status error: {e.response.status_code} {e.response.text}"}
    except httpx.TimeoutException:
        return {"error": "Request timed out. The backend server may be slow or unavailable."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e.__class__.__name__}: {str(e)}"}


@mcp.tool()
def filterPlayers(filters: str, limit: int = 100):
    """
    Filter the full ~500-player dataset using a pandas query expression and
    return up to `limit` matching rows.

    PURPOSE — SMART CONTEXT MANAGEMENT:
    Loading all 500 players at once floods the context window and wastes tokens.
    Instead, use describePlayersDF() first to understand the data distribution,
    then craft a precise filter here to fetch only the players you actually need.
    The default limit is 100 — prefer tight filters so you get far fewer rows.
    Only raise the limit when the user explicitly needs a broad list.

    AVAILABLE COLUMNS (valid names for filter expressions):
    -------------------------------------------------------
    player_name, pro_team, positions, team_id, status
    injured, fantasy_team_name
    season_rating, last7_rating, last15_rating, last30_rating
    pts, reb, ast, stl, blk, three_pm, fgm, fga, ftm, fta, minutes, gp
    fg_percentage, ft_percentage

    NOTE: All stats (pts, reb, ast, …) are SEASON TOTALS.
    For per-game averages use arithmetic inside the expression:
      pts / gp > 20   →  players averaging 20+ points per game

    FILTER EXPRESSION SYNTAX (pandas .query() string):
      - Comparisons : pts / gp > 20
      - Equality    : status == 'FREEAGENT'
      - Membership  : pro_team in ['LAL', 'BOS']
      - Combine     : status == 'FREEAGENT' and pts / gp > 15 and gp >= 30
      - Contains    : player_name.str.contains('James')

    COMMON FILTER EXAMPLES:
      "status == 'FREEAGENT'"                                        — all free agents
      "status == 'FREEAGENT' and pts / gp > 15"                     — FA averaging 15+ PPG
      "injured == False and status == 'FREEAGENT'"                   — healthy free agents only
      "season_rating > 10 and injured == False"                      — high-rated healthy players
      "last7_rating > 15 and status == 'FREEAGENT'"                  — hot FAs last 7 days
      "team_id == 5"                                                  — all players on fantasy team 5
      "status != 'ONTEAM'"                                            — free agents + waivers
      "blk / gp > 1.5 and gp >= 20"                                  — shot-blockers with enough GP
      "fg_percentage > 0.50 and fga / gp > 5"                        — efficient shooters
      "ast / gp > 6 and status == 'FREEAGENT'"                       — playmaking FAs

    TRADE MISSION PLAYBOOK
    -------------------------------------------------------
    Follow this whenever the user asks about trades, swaps, offers, or improving
    their team by exchanging players.

    HARD FILTERS — use in EVERY filterPlayers call during trade analysis:
      injured == False
          — UNLESS the user explicitly named an injured player themselves.
            In that case include them but warn: "This player is currently injured."
      season_rating == season_rating
          — NaN-safe trick: silently drops players with no rating data
            (rarely played, just signed). Never include them in proposals.

    FAIRNESS RULES:
      FAIR       : |A.season_rating - B.season_rating| / A.season_rating < 0.15
      SLIGHT GAP : 15-25% difference — mention it but may still recommend
      UNFAIR     : > 25% difference — do NOT recommend
      FORM CHECK : last30_rating also within ~15% confirms current form matches
      SMALL SAMPLE: flag gp < 20 as "small sample — use with caution"

    DETERMINE MODE from the user's message:
      MODE A — user named a player they want to GIVE AWAY
      MODE B — user named a player they want to ACQUIRE
      MODE C — no preference ("suggest a trade", "help me", "I don't know")

    MODE A — give away a specific player:
      Step 1: filterPlayers("player_name.str.contains('<name>')") — confirm player,
              note season_rating + last30_rating
      Step 2: getAveragesLeagueRankings() — find your weak roto categories
      Step 3: describePlayersDF() — understand league rating distribution
      Step 4: filterPlayers("status=='ONTEAM' and injured==False
               and season_rating==season_rating
               and season_rating >= <seller*0.85> and season_rating <= <seller*1.15>")
      Step 5: from results, narrow to last30_rating also within ~15% of seller's
      Step 6: prefer candidates whose stats address your WEAK categories; exclude own team
      Step 7: present top 3-5 — fantasy_team_name, ratings, category gain/loss, fairness

    MODE B — acquire a specific player:
      Step 1: filterPlayers to confirm target, get season_rating + last30_rating
      Step 2: getTeamDetails(user_team_id) — see your full roster
      Step 3: find your players within 15% of target's season_rating AND last30_rating
      Step 4: getAveragesLeagueRankings() — offer from your STRONG categories
      Step 5: present top 2-3 offers — category gain/loss + fairness label

    MODE C — full auto:
      Step 1: getAveragesLeagueRankings() — find 2-3 weakest + 2-3 strongest categories
      Step 2: getTeamDetails(user_team_id) — full roster + ratings
      Step 3: describePlayersDF() — understand league distributions (75th pct = "league strong")
      Step 4: identify sell candidates from STRONG categories, not injured, have season_rating
      Step 5: filterPlayers("status=='ONTEAM' and injured==False and season_rating==season_rating")
              — all healthy rated rostered players; exclude own team_id
      Step 6: match — season_rating within 15%, last30_rating within 15%, fills weak cats
      Step 7: rank by category gain score
      Step 8: present top 3 — fantasy_team_name, ratings, gain/loss per category, fairness

    REMINDERS:
      - Never propose your own players on both sides
      - Always show fantasy_team_name so user knows who to contact
      - If no fair trade exists, say so explicitly
      - Never hallucinate player names — always confirm via filterPlayers first

    Args:
        filters : pandas query string (see examples above). Pass "" to return
                  the top `limit` rows unfiltered (not recommended for large results).
        limit   : maximum number of rows to return (default 100, max 500).
                  Keep this low unless the user explicitly needs a wider list.

    Returns:
        A list of player dicts, each with keys:
        player_name, pro_team, positions, team_id, status,
        injured, fantasy_team_name,
        season_rating, last7_rating, last15_rating, last30_rating,
        pts, reb, ast, stl, blk, three_pm, fgm, fga, ftm, fta,
        fg_percentage, ft_percentage, minutes, gp
    """
    try:
        df = _build_players_df()

        if filters and filters.strip():
            df = df.query(filters)

        df = df.head(limit)
        return df.to_dict(orient="records")

    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP status error: {e.response.status_code} {e.response.text}"}
    except httpx.TimeoutException:
        return {"error": "Request timed out. The backend server may be slow or unavailable."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e.__class__.__name__}: {str(e)}"}