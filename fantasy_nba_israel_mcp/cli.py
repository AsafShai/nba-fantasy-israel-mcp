"""CLI entry point for Fantasy NBA Israel League."""

import json
from typing import Optional

import typer

from fantasy_nba_israel_mcp.core import (
    get_average_stats,
    get_averages_league_rankings,
    get_league_shots_stats,
    get_snapshots,
    get_team_details,
    get_teams,
)

app = typer.Typer(name="fantasy-nba", help="Fantasy NBA Israel League CLI", add_completion=False)

VALID_STATS = "pts, reb, ast, stl, blk, three_pm, fg_pct, ft_pct, gp, fgm, fga, ftm, fta"


def _output(data) -> None:
    if isinstance(data, dict) and "error" in data:
        typer.echo(data["error"], err=True)
        raise typer.Exit(code=1)
    typer.echo(json.dumps(data, indent=2, ensure_ascii=False))


@app.command()
def rankings(
    order: str = typer.Option("desc", help="Sort order: 'desc' (best first) or 'asc' (worst first)"),
):
    """Get rotisserie league rankings for all teams."""
    _output(get_averages_league_rankings(order))


@app.command()
def teams():
    """List all teams with their IDs."""
    _output(get_teams())


@app.command()
def stats(
    normalized: bool = typer.Option(False, "--normalized/--raw", help="Return 0-1 normalized values instead of raw stats"),
):
    """Get per-game stat averages for all teams."""
    _output(get_average_stats(normalized))


@app.command()
def team(
    team_id: int = typer.Argument(..., help="Team ID (use 'teams' command to find IDs)"),
):
    """Get full details for one team: roster, rankings, and stats."""
    _output(get_team_details(team_id))


@app.command()
def shots():
    """Get cumulative shooting stats (FG/FT totals and percentages) for all teams."""
    _output(get_league_shots_stats())


@app.command()
def snapshots(
    date: Optional[str] = typer.Option(None, "--date", help="Filter by date (YYYY-MM-DD)"),
    team_id: Optional[int] = typer.Option(None, "--team-id", help="Filter by team ID"),
    stat: Optional[str] = typer.Option(None, "--stat", help=f"Sort by stat descending. Options: {VALID_STATS}"),
    limit: int = typer.Option(10, "--limit", help="Max rows to return"),
):
    """Query historical daily snapshots with filters."""
    _output(get_snapshots(date=date, team_id=team_id, stat=stat, limit=limit))
