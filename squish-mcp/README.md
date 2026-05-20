# squish-mcp-server

MCP Server für Squish GUI Test Automation.

## Installation

```bash
cd /home/runner/work/CodePreviewProject/CodePreviewProject/squish-mcp
pip install -e .
```

After installation, the `squish-mcp` command is available globally in your active Python environment.

## CLI Commands

```bash
squish-mcp status
squish-mcp generate "Click login, type user and password, then submit"
squish-mcp execute
squish-mcp find-object loginButton --names-file C:/path/to/names.py
squish-mcp find-by-text "Login" --names-file C:/path/to/names.py
squish-mcp find-by-type QPushButton --names-file C:/path/to/names.py
squish-mcp troubleshoot
squish-mcp server start
squish-mcp server stop
```

## Notes

- The CLI uses Rich-based formatting (tables, colors, status icons, and panels) for readable terminal output.
- Commands include clear error reporting with helpful visual feedback.
- Existing server logic in `mcp_server.py` remains unchanged and is reused by the CLI.
