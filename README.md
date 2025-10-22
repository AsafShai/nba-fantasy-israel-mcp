# Fantasy NBA Israel League MCP

A Model Context Protocol (MCP) server that provides tools for accessing our Fantasy NBA Israel League statistics and rankings.

## Description

This MCP server connects to a specific Fantasy NBA League API (Fantasy NBA Israel League) and provides tools to retrieve team rankings, player statistics, and detailed analytics.

**Note:** This server is configured for a specific private league and connects to its dedicated API endpoint. It is not a general-purpose tool for any Fantasy NBA league - it's designed specifically for our league's data structure and API.

## Features

- **Get Average League Rankings**: Retrieve team rankings with detailed statistics
  - Sort in ascending or descending order
  - Detailed stats per category (FG%, FT%, 3PM, AST, REB, STL, BLK, PTS, GP)
  - Total points and rank for each team
- **Get Teams**: Retrieve list of all teams in the league
- **Get Average Stats**: Get team statistics in a user-friendly format with stats mapped by category
  - Option to retrieve raw or normalized (0-1 scale) data
  - Includes games played (GP) for each team
- **Get Team Details**: Retrieve comprehensive details for a specific team
  - Team statistics (totals and averages)
  - Complete roster with player stats including minutes played
  - ESPN team page URL
  - Shot chart stats and ranking information
  - Category ranks across all statistical categories
- **Get All Players**: Retrieve all players in the league with comprehensive statistics
  - Includes minutes played and games played for each player
- **Get League Shots Stats**: Retrieve league-wide shooting statistics for all teams

## Prerequisites

Before using this MCP server, you'll need:

1. **`uv` or `uvx`**: A fast Python package installer and runner
   - Install from [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/)
   - On macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - On Windows: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`

2. **An MCP-compatible client**: Choose one of the following or similar:
   - [Claude Desktop](https://claude.ai/download) - AI assistant with MCP support
   - [Cursor](https://cursor.sh/) - AI-powered code editor
   - [VSCode](https://code.visualstudio.com/) with [GitHub Copilot Chat](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot-chat)
   - [Cline](https://github.com/cline/cline) - VSCode extension for AI assistance
   - Any other MCP-compatible application

## Usage

### As an MCP Server

This server works with any MCP-compatible client (Claude Desktop, Cursor, Cline, VSCode with GitHub Copilot Chat, etc.). Add the following configuration to your client's MCP settings file:

```json
{
  "mcpServers": {
    "fantasynbaleague": {
      "command": "uvx",
      "args": ["fantasy-nba-israel-mcp"]
    }
  }
}
```

**Common configuration file locations:**
- **Claude Desktop**: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows)
- **Cursor**: `.cursor/mcp.json` in your project or global settings
- **Cline**: Use the MCP settings UI or edit `cline_mcp_settings.json`
- **VSCode**: `.vscode/mcp.json` in your workspace

### Local Development

For local development and testing, you can run the MCP server in development mode:

```bash
uv run mcp dev fantasy_nba_israel_mcp/server.py
```

This will start an interactive MCP inspector where you can test your tools.

### Standalone Testing

```python
from fantasy_nba_israel_mcp import mcp

# Run the MCP server
if __name__ == "__main__":
    mcp.run()
```

Or run directly:

```bash
python -m fantasy_nba_israel_mcp
```

## Available Tools

### getAveragesLeagueRankings

Get the average league rankings from the API.

**Parameters:**
- `order` (str, optional): Sort order for rankings
  - `"desc"` = best to worst (top teams first) - Default
  - `"asc"` = worst to best (bottom teams first)

**Returns:**
A list of teams with their rankings, total points, and stats per category.

**Example Response:**
```json
[
  {
    "team": {
      "team_id": 1,
      "team_name": "Team Name"
    },
    "fg_percentage": 0.456,
    "ft_percentage": 0.789,
    "three_pm": 12.5,
    "ast": 24.3,
    "reb": 45.6,
    "stl": 8.2,
    "blk": 5.4,
    "pts": 112.3,
    "gp": 55,
    "total_points": 36,
    "rank": 1
  }
]
```

### getTeams

Get the list of all teams in the league.

**Parameters:**
None

**Returns:**
A list of teams with their IDs and names.

**Example Response:**
```json
[
  {
    "team_id": 1,
    "team_name": "First team example"
  },
  {
    "team_id": 2,
    "team_name": "Another team name"
  }
]
```

### getAverageStats

Get average stats for all teams in a user-friendly format with stats mapped by category name.

**Parameters:**
- `use_normalized` (bool, optional): If `true`, returns normalized data (0-1 scale). If `false`, returns raw stat values. Default is `false`.

**Returns:**
A list of teams with their stats mapped by category name.

**Example Response:**
```json
[
  {
    "team": {
      "team_id": 1,
      "team_name": "First team example"
    },
    "stats": {
      "FG%": 0.48532033,
      "FT%": 0.80961071,
      "3PM": 1.71184371,
      "AST": 4.28449328,
      "REB": 6.75579976,
      "STL": 1.13919414,
      "BLK": 0.72405372,
      "PTS": 17.5970696,
      "GP": 55
    }
  }
]
```

### getTeamDetails

Get comprehensive details for a specific team including statistics, roster, and rankings.

**Parameters:**
- `team_id` (int): The ID of the team to get details for

**Returns:**
Comprehensive team information including team stats, ESPN URL, shot chart, rankings, and full roster.

**Example Response:**
```json
{
  "team": {
    "team_id": 1,
    "team_name": "Team Name"
  },
  "espn_url": "https://fantasy.espn.com/basketball/team?leagueId=123&teamId=1",
  "shot_chart": {
    "team": {"team_id": 1, "team_name": "Team Name"},
    "fgm": 14,
    "fga": 23,
    "fg_percentage": 0.608,
    "ftm": 7,
    "fta": 12,
    "ft_percentage": 0.583,
    "gp": 2
  },
  "raw_averages": {
    "fg_percentage": 0.608,
    "ft_percentage": 0.583,
    "three_pm": 0.5,
    "ast": 4.5,
    "reb": 5.5,
    "stl": 1.0,
    "blk": 0.5,
    "pts": 18.0,
    "gp": 2,
    "team": {"team_id": 1, "team_name": "Team Name"}
  },
  "ranking_stats": {
    "team": {"team_id": 1, "team_name": "Team Name"},
    "fg_percentage": 12.0,
    "ft_percentage": 5.0,
    "three_pm": 5.0,
    "ast": 8.0,
    "reb": 7.0,
    "stl": 6.0,
    "blk": 9.0,
    "pts": 9.0,
    "gp": 2,
    "total_points": 61.0,
    "rank": 6
  },
  "category_ranks": {
    "FG%": 12,
    "FT%": 5,
    "3PM": 5,
    "AST": 8,
    "REB": 7,
    "STL": 6,
    "BLK": 9,
    "PTS": 9
  },
  "players": [
    {
      "player_name": "LeBron James",
      "pro_team": "LAL",
      "positions": ["SF", "PF"],
      "stats": {
        "pts": 25.4,
        "reb": 7.3,
        "ast": 7.4,
        "stl": 1.3,
        "blk": 0.5,
        "fgm": 9.5,
        "fga": 18.5,
        "ftm": 4.8,
        "fta": 6.3,
        "fg_percentage": 0.513,
        "ft_percentage": 0.762,
        "three_pm": 2.1,
        "minutes": 35.2,
        "gp": 55
      },
      "team_id": 1
    }
  ]
}
```

### getAllPlayers

Get all players in the league with comprehensive statistics.

**Parameters:**
None

**Returns:**
A list of all players with their stats and team association.

**Example Response:**
```json
[
  {
    "player_name": "LeBron James",
    "pro_team": "LAL",
    "positions": ["SF", "PF"],
    "team_id": 1,
    "stats": {
      "pts": 25.4,
      "reb": 7.3,
      "ast": 7.4,
      "stl": 1.3,
      "blk": 0.5,
      "fgm": 9.5,
      "fga": 18.5,
      "ftm": 4.8,
      "fta": 6.3,
      "fg_percentage": 0.513,
      "ft_percentage": 0.762,
      "three_pm": 2.1,
      "minutes": 35.2,
      "gp": 55
    }
  }
]
```

### getLeagueShotsStats

Get league-wide shooting statistics for all teams.

**Parameters:**
None

**Returns:**
League-wide shooting statistics with field goal and free throw data for each team.

**Example Response:**
```json
{
  "shots": [
    {
      "team": {
        "team_id": 1,
        "team_name": "Team Name"
      },
      "fgm": 14,
      "fga": 23,
      "fg_percentage": 0.608,
      "ftm": 7,
      "fta": 12,
      "ft_percentage": 0.583,
      "gp": 2
    },
    {
      "team": {
        "team_id": 2,
        "team_name": "Another Team"
      },
      "fgm": 12,
      "fga": 20,
      "fg_percentage": 0.600,
      "ftm": 8,
      "fta": 10,
      "ft_percentage": 0.800,
      "gp": 2
    }
  ]
}
```

## Requirements

- Python >= 3.10
- httpx >= 0.28.1
- mcp[cli] >= 1.18.0

## Development

To run the server locally for development and testing:

```bash
# Install dependencies
uv sync

# Run in development mode with MCP inspector
uv run mcp dev fantasy_nba_israel_mcp/server.py
```

The MCP inspector will provide an interactive interface to test all your tools.

## Author

Asaf Shai (asafshai211@gmail.com)

## Support

For issues and questions, please open an issue on the GitHub repository.

