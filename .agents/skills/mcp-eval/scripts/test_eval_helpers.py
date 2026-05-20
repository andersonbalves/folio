"""Unit tests for pure helper functions in eval_mcp.py."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Load eval_mcp.py as module without executing main()
_spec = importlib.util.spec_from_file_location(
    "eval_mcp",
    Path(__file__).parent / "eval_mcp.py",
)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules["eval_mcp"] = _mod  # required for @dataclass on Python 3.14
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

load_scenario = _mod.load_scenario
mcp_tool_to_anthropic = _mod.mcp_tool_to_anthropic
check_trigger_assertions = _mod.check_trigger_assertions
Scenario = _mod.Scenario
ExpectedTool = _mod.ExpectedTool
ToolCall = _mod.ToolCall


class TestLoadScenario:
    def test_loads_all_fields(self, tmp_path):
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(
            'id: "001"\n'
            'name: "Test scenario"\n'
            'question: "What topics?"\n'
            "expected_tools:\n"
            "  - name: list_topics\n"
            "    required: true\n"
            "quality_criteria:\n"
            '  - "Response mentions topics"\n'
        )
        scenario = load_scenario(yaml_file)
        assert scenario.id == "001"
        assert scenario.name == "Test scenario"
        assert scenario.question == "What topics?"
        assert len(scenario.expected_tools) == 1
        assert scenario.expected_tools[0].name == "list_topics"
        assert scenario.expected_tools[0].required is True
        assert scenario.quality_criteria == ["Response mentions topics"]

    def test_required_field_defaults_to_true(self, tmp_path):
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(
            'id: "002"\nname: "T"\nquestion: "Q"\n'
            "expected_tools:\n  - name: search_docs\nquality_criteria: []\n"
        )
        scenario = load_scenario(yaml_file)
        assert scenario.expected_tools[0].required is True

    def test_empty_quality_criteria(self, tmp_path):
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(
            'id: "003"\nname: "T"\nquestion: "Q"\nexpected_tools: []\nquality_criteria: []\n'
        )
        scenario = load_scenario(yaml_file)
        assert scenario.quality_criteria == []


class TestMcpToolToAnthropic:
    def test_converts_full_schema(self):
        tool = MagicMock()
        tool.name = "list_topics"
        tool.description = "List available topics"
        tool.inputSchema = {
            "type": "object",
            "properties": {"category": {"type": "string"}},
        }
        result = mcp_tool_to_anthropic(tool)
        assert result["name"] == "list_topics"
        assert result["description"] == "List available topics"
        assert result["input_schema"] == tool.inputSchema

    def test_none_description_becomes_empty_string(self):
        tool = MagicMock()
        tool.name = "get_document"
        tool.description = None
        tool.inputSchema = {"type": "object", "properties": {}}
        result = mcp_tool_to_anthropic(tool)
        assert result["description"] == ""

    def test_input_schema_key_not_parameters(self):
        tool = MagicMock()
        tool.name = "search_docs"
        tool.description = "Search"
        tool.inputSchema = {"type": "object"}
        result = mcp_tool_to_anthropic(tool)
        assert "input_schema" in result
        assert "parameters" not in result


class TestCheckTriggerAssertions:
    def test_required_tool_called_passes(self):
        tool_calls = [ToolCall(tool="list_topics", args={}, result_len=100)]
        expected = [ExpectedTool(name="list_topics", required=True)]
        result = check_trigger_assertions(tool_calls, expected)
        assert result.required_called is True
        assert result.passed is True
        assert result.missing == []

    def test_required_tool_not_called_fails(self):
        tool_calls = []
        expected = [ExpectedTool(name="list_topics", required=True)]
        result = check_trigger_assertions(tool_calls, expected)
        assert result.required_called is False
        assert result.passed is False
        assert "list_topics" in result.missing

    def test_unexpected_tool_is_warning_not_failure(self):
        tool_calls = [
            ToolCall(tool="list_topics", args={}, result_len=100),
            ToolCall(tool="search_docs", args={"query": "x"}, result_len=50),
        ]
        expected = [ExpectedTool(name="list_topics", required=True)]
        result = check_trigger_assertions(tool_calls, expected)
        assert result.required_called is True
        assert result.unexpected_called is True
        assert "search_docs" in result.unexpected
        assert result.passed is True  # unexpected = warning only

    def test_optional_tool_missing_does_not_fail(self):
        tool_calls = [ToolCall(tool="list_topics", args={}, result_len=100)]
        expected = [
            ExpectedTool(name="list_topics", required=True),
            ExpectedTool(name="get_document", required=False),
        ]
        result = check_trigger_assertions(tool_calls, expected)
        assert result.passed is True
        assert result.missing == []

    def test_multiple_required_tools_all_must_be_called(self):
        tool_calls = [ToolCall(tool="search_docs", args={}, result_len=50)]
        expected = [
            ExpectedTool(name="search_docs", required=True),
            ExpectedTool(name="get_document", required=True),
        ]
        result = check_trigger_assertions(tool_calls, expected)
        assert result.passed is False
        assert "get_document" in result.missing
