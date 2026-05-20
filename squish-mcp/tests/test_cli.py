import unittest
from unittest.mock import patch

from click.testing import CliRunner
from cli import main


class FakeServer:
    def __init__(self):
        self._status = {
            "server_host": "localhost",
            "server_port": 8000,
            "squish_version": "8.0.0",
            "squish_port": 4322,
            "agents_initialized": {
                "object_spy": True,
                "test_generator": False,
                "intelligent_test_generator": False,
                "executor": True,
            },
        }

    def get_status(self):
        return self._status

    def initialize_intelligent_test_generator(self):
        return {"status": "success"}

    def generate_intelligent_test(self, description):
        return {"status": "success", "test_code": f"# generated for: {description}"}


class CLITestCase(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    @patch("cli._safe_server", return_value=FakeServer())
    def test_status_command_renders_agents(self, _mock_server):
        result = self.runner.invoke(main, ["status"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Squish MCP Status", result.output)
        self.assertIn("Object Spy", result.output)
        self.assertIn("✅ Initialized", result.output)
        self.assertIn("❌ Not initialized", result.output)

    @patch("cli._safe_server", return_value=FakeServer())
    def test_generate_command_shows_success(self, _mock_server):
        result = self.runner.invoke(main, ["generate", "login test"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Test generated successfully", result.output)
        self.assertIn("generated for: login test", result.output)


if __name__ == "__main__":
    unittest.main()
