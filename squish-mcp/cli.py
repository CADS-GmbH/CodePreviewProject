"""Command-line interface for Squish MCP Server."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.table import Table

console = Console()


class CLIError(Exception):
    """Raised when a CLI command cannot complete successfully."""


def _load_server_class():
    """Load and return the SquishMCPServer class lazily."""
    try:
        from mcp_server import SquishMCPServer

        return SquishMCPServer
    except Exception as exc:
        raise CLIError(f"Unable to import Squish MCP Server: {exc}") from exc


def _show_result_banner(title: str, message: str, success: bool = True) -> None:
    """Render a success or error banner panel."""
    icon = "✅" if success else "❌"
    style = "green" if success else "red"
    console.print(Panel.fit(f"{icon} {message}", title=title, border_style=style))


def _safe_server() -> Any:
    """Create server instance with user-friendly error output."""
    server_cls = _load_server_class()
    try:
        return server_cls()
    except Exception as exc:
        raise CLIError(f"Failed to initialize server: {exc}") from exc


def _ensure_object_spy(server: Any, names_file: Optional[Path]) -> Dict[str, Any]:
    """Initialize object spy agent using names.py path."""
    if names_file:
        path = names_file
    else:
        config = server.get_config()
        path = Path(config["TEST_SUITE"]) / "names.py"

    return server.initialize_object_spy(str(path))


def _print_json_panel(title: str, data: Dict[str, Any]) -> None:
    """Print dictionary data in a readable panel."""
    payload = json.dumps(data, indent=2, ensure_ascii=False)
    console.print(Panel(payload, title=title, border_style="cyan"))


def _format_agent_name(name: str) -> str:
    """Format internal agent key names for user-facing output."""
    return name.replace("_", " ").title()


@click.group()
def main() -> None:
    """Squish MCP command-line tools."""


@main.command("status")
def status() -> None:
    """Show server status and initialized agents."""
    try:
        server = _safe_server()
        data = server.get_status()

        table = Table(title="⚙️ Squish MCP Status", box=box.ROUNDED, show_header=True, header_style="bold cyan")
        table.add_column("Property", style="white")
        table.add_column("Value", style="green")
        table.add_row("Server", f"{data.get('server_host')}:{data.get('server_port')}")
        table.add_row("Squish Version", str(data.get("squish_version", "unknown")))
        table.add_row("Squish Port", str(data.get("squish_port", "unknown")))

        console.print(table)

        agents = data.get("agents_initialized", {})
        agent_table = Table(title="🤖 Agents", box=box.SIMPLE_HEAVY)
        agent_table.add_column("Agent")
        agent_table.add_column("Status", justify="center")
        for name, initialized in agents.items():
            agent_table.add_row(_format_agent_name(name), "✅ Initialized" if initialized else "❌ Not initialized")
        console.print(agent_table)
    except CLIError as exc:
        _show_result_banner("Status", str(exc), success=False)
        raise click.Abort() from exc


@main.command("generate")
@click.argument("description")
@click.option("--output", "output_file", type=click.Path(path_type=Path), help="Optional output file for generated test code.")
def generate(description: str, output_file: Optional[Path]) -> None:
    """Generate test code from a natural language description."""
    try:
        server = _safe_server()
        init_result = server.initialize_intelligent_test_generator()
        if init_result.get("status") != "success":
            raise CLIError(init_result.get("message", "Failed to initialize intelligent test generator"))

        result = server.generate_intelligent_test(description)
        if result.get("status") != "success":
            raise CLIError(result.get("message", "Could not generate test"))

        test_code = result.get("test_code", "")
        _show_result_banner("Generate", "Test generated successfully")
        if test_code:
            console.print(Syntax(test_code, "python", theme="monokai", line_numbers=True))
        else:
            _print_json_panel("Generate Result", result)

        if output_file:
            save_result = server.save_test_code(test_code, str(output_file))
            if save_result.get("status") != "success":
                raise CLIError(save_result.get("message", "Failed to save generated test"))
            _show_result_banner("Generate", f"Saved test code to {output_file}")
    except CLIError as exc:
        _show_result_banner("Generate", str(exc), success=False)
        raise click.Abort() from exc


@main.command("execute")
def execute() -> None:
    """Execute tests through the Squish executor."""
    try:
        server = _safe_server()
        init_result = server.initialize_executor()
        if init_result.get("status") != "success":
            raise CLIError(init_result.get("message", "Failed to initialize executor"))

        result = server.execute_test()
        success = result.get("status") == "success"
        _show_result_banner("Execute", "Test execution completed" if success else "Test execution failed", success=success)
        _print_json_panel("Execution Result", result)

        if not success:
            raise click.Abort()
    except CLIError as exc:
        _show_result_banner("Execute", str(exc), success=False)
        raise click.Abort() from exc


@main.command("find-object")
@click.argument("name")
@click.option("--names-file", type=click.Path(path_type=Path, exists=True), help="Path to names.py file.")
def find_object(name: str, names_file: Optional[Path]) -> None:
    """Find a UI object by object name."""
    try:
        server = _safe_server()
        init_result = _ensure_object_spy(server, names_file)
        if init_result.get("status") != "success":
            raise CLIError(init_result.get("message", "Could not initialize object spy"))

        result = server.find_object_by_name(name)
        if result.get("status") == "success":
            _show_result_banner("Find Object", f"Found object '{name}'")
            _print_json_panel("Object", result.get("object", {}))
            return

        if result.get("status") == "not_found":
            _show_result_banner("Find Object", f"Object '{name}' not found", success=False)
            raise click.Abort()

        raise CLIError(result.get("message", "Search failed"))
    except CLIError as exc:
        _show_result_banner("Find Object", str(exc), success=False)
        raise click.Abort() from exc


def _render_find_results(title: str, result: Dict[str, Any]) -> None:
    """Render tabular object search results."""
    table = Table(title=title, box=box.ROUNDED)
    table.add_column("#", justify="right")
    table.add_column("Name", style="cyan")
    table.add_column("Details", style="white")

    items = result.get("results", [])
    for idx, item in enumerate(items, start=1):
        item_name = item.get("name", "-") if isinstance(item, dict) else str(item)
        details = json.dumps(item, ensure_ascii=False) if isinstance(item, dict) else str(item)
        table.add_row(str(idx), item_name, details)

    console.print(table)


@main.command("find-by-text")
@click.argument("text")
@click.option("--names-file", type=click.Path(path_type=Path, exists=True), help="Path to names.py file.")
def find_by_text(text: str, names_file: Optional[Path]) -> None:
    """Find objects by text content."""
    try:
        server = _safe_server()
        init_result = _ensure_object_spy(server, names_file)
        if init_result.get("status") != "success":
            raise CLIError(init_result.get("message", "Could not initialize object spy"))

        result = server.find_objects_by_text(text)
        if result.get("status") != "success":
            raise CLIError(result.get("message", "Search failed"))

        _show_result_banner("Find by Text", f"Found {result.get('count', 0)} object(s)")
        _render_find_results("🔎 Matches by Text", result)
    except CLIError as exc:
        _show_result_banner("Find by Text", str(exc), success=False)
        raise click.Abort() from exc


@main.command("find-by-type")
@click.argument("obj_type")
@click.option("--names-file", type=click.Path(path_type=Path, exists=True), help="Path to names.py file.")
def find_by_type(obj_type: str, names_file: Optional[Path]) -> None:
    """Find objects by object type."""
    try:
        server = _safe_server()
        init_result = _ensure_object_spy(server, names_file)
        if init_result.get("status") != "success":
            raise CLIError(init_result.get("message", "Could not initialize object spy"))

        result = server.find_objects_by_type(obj_type)
        if result.get("status") != "success":
            raise CLIError(result.get("message", "Search failed"))

        _show_result_banner("Find by Type", f"Found {result.get('count', 0)} object(s)")
        _render_find_results("🧩 Matches by Type", result)
    except CLIError as exc:
        _show_result_banner("Find by Type", str(exc), success=False)
        raise click.Abort() from exc


@main.command("troubleshoot")
def troubleshoot() -> None:
    """Interactively troubleshoot a test error."""
    try:
        server = _safe_server()
        user_input = Prompt.ask("📝 Describe your issue")
        error_message = Prompt.ask("❌ Error message", default="")
        test_code = Prompt.ask("📄 Test code snippet (optional)", default="")
        environment_context = Prompt.ask("🌍 Environment context (optional)", default="")
        normalized_error_message = error_message or None
        normalized_test_code = test_code or None
        normalized_environment_context = environment_context or None

        result = server.troubleshoot_test_error(
            user_input=user_input,
            error_message=normalized_error_message,
            test_code=normalized_test_code,
            environment_context=normalized_environment_context,
        )
        success = result.get("status") == "success"
        _show_result_banner("Troubleshoot", "Analysis complete" if success else "Could not complete analysis", success=success)
        _print_json_panel("Troubleshooting", result)

        if not success:
            raise click.Abort()
    except CLIError as exc:
        _show_result_banner("Troubleshoot", str(exc), success=False)
        raise click.Abort() from exc


@main.group("server")
def server_group() -> None:
    """Manage the Squish server lifecycle."""


@server_group.command("start")
def server_start() -> None:
    """Start the Squish server."""
    try:
        server = _safe_server()
        init_result = server.initialize_executor()
        if init_result.get("status") != "success":
            raise CLIError(init_result.get("message", "Failed to initialize executor"))

        result = server.start_squish_server()
        success = result.get("status") == "success"
        _show_result_banner("Server Start", result.get("message", "Done"), success=success)
        if not success:
            raise click.Abort()
    except CLIError as exc:
        _show_result_banner("Server Start", str(exc), success=False)
        raise click.Abort() from exc


@server_group.command("stop")
def server_stop() -> None:
    """Stop the Squish server."""
    try:
        server = _safe_server()
        init_result = server.initialize_executor()
        if init_result.get("status") != "success":
            raise CLIError(init_result.get("message", "Failed to initialize executor"))

        result = server.stop_squish_server()
        success = result.get("status") == "success"
        _show_result_banner("Server Stop", result.get("message", "Done"), success=success)
        if not success:
            raise click.Abort()
    except CLIError as exc:
        _show_result_banner("Server Stop", str(exc), success=False)
        raise click.Abort() from exc


if __name__ == "__main__":
    main()
