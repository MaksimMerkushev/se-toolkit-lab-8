"""Canonical package for the LMS MCP server."""

from mcp_lms.client import LMSClient
from mcp_lms.server import main

__all__ = ["LMSClient", "main"]
