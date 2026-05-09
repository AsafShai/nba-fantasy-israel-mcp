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
from fantasy_nba_israel_mcp.core import (
    get_averages_league_rankings,
    get_teams as _get_teams,
    get_average_stats,
    get_team_details,
    get_league_shots_stats,
    query_team_scores_snapshots as _query_snapshots,
)

mcp = FastMCP("fantasy-nba-israel-mcp")


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
    return get_averages_league_rankings(order)


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
    return _get_teams()


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
    return get_average_stats(use_normalized)


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
    return get_team_details(team_id)


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
    return get_league_shots_stats()


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
    return _query_snapshots(query)
