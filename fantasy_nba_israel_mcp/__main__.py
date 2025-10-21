"""Entry point for running the MCP server as a module."""

from fantasy_nba_israel_mcp.server import mcp


def main():
    """Main entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()

