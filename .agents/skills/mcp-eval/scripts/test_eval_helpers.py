"""Unit tests for pure helper functions in eval_mcp.py."""

import importlib.util
import json
import sys
from pathlib import Path

# Load eval_mcp.py as module without executing main()
_spec = importlib.util.spec_from_file_location(
    "eval_mcp",
    Path(__file__).parent / "eval_mcp.py",
)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules["eval_mcp"] = _mod  # required for @dataclass on Python 3.14
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

load_scenario = _mod.load_scenario
check_trigger_assertions = _mod.check_trigger_assertions
parse_stream_json = _mod.parse_stream_json
_normalize_tool_name = _mod._normalize_tool_name
_build_mcp_config = _mod._build_mcp_config
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


class TestNormalizeToolName:
    def test_strips_mcp_server_prefix(self):
        assert _normalize_tool_name("mcp__folio__list_topics") == "list_topics"

    def test_strips_any_server_name(self):
        assert _normalize_tool_name("mcp__other_server__search_docs") == "search_docs"

    def test_non_mcp_name_unchanged(self):
        assert _normalize_tool_name("Read") == "Read"
        assert _normalize_tool_name("Bash") == "Bash"

    def test_mcp_prefix_without_tool_unchanged(self):
        assert _normalize_tool_name("mcp__folio") == "mcp__folio"


class TestParseStreamJson:
    def test_empty_output_returns_empty(self):
        tool_calls, answer = parse_stream_json("")
        assert tool_calls == []
        assert answer == ""

    def test_result_only_no_tools(self):
        output = json.dumps({"type": "result", "result": "The answer is 42"}) + "\n"
        tool_calls, answer = parse_stream_json(output)
        assert tool_calls == []
        assert answer == "The answer is 42"

    def test_single_tool_call_with_result_len(self):
        lines = [
            json.dumps(
                {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {"type": "tool_use", "id": "tu_1", "name": "list_topics", "input": {}}
                        ]
                    },
                }
            ),
            json.dumps({"type": "tool", "id": "tu_1", "output": "topic1\ntopic2\ntopic3"}),
            json.dumps({"type": "result", "result": "Topics found: topic1, topic2, topic3"}),
        ]
        tool_calls, answer = parse_stream_json("\n".join(lines))
        assert len(tool_calls) == 1
        assert tool_calls[0].tool == "list_topics"
        assert tool_calls[0].args == {}
        assert tool_calls[0].result_len == len("topic1\ntopic2\ntopic3")
        assert answer == "Topics found: topic1, topic2, topic3"

    def test_multiple_tool_calls_in_sequence(self):
        lines = [
            json.dumps(
                {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {
                                "type": "tool_use",
                                "id": "tu_1",
                                "name": "search_docs",
                                "input": {"query": "kubernetes"},
                            }
                        ]
                    },
                }
            ),
            json.dumps({"type": "tool", "id": "tu_1", "output": "result1\nresult2"}),
            json.dumps(
                {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {
                                "type": "tool_use",
                                "id": "tu_2",
                                "name": "get_document",
                                "input": {"path": "/docs/k8s.md"},
                            }
                        ]
                    },
                }
            ),
            json.dumps({"type": "tool", "id": "tu_2", "output": "# Kubernetes\n...content..."}),
            json.dumps({"type": "result", "result": "Here is the kubernetes doc"}),
        ]
        tool_calls, answer = parse_stream_json("\n".join(lines))
        assert len(tool_calls) == 2
        assert tool_calls[0].tool == "search_docs"
        assert tool_calls[0].args == {"query": "kubernetes"}
        assert tool_calls[1].tool == "get_document"
        assert tool_calls[1].args == {"path": "/docs/k8s.md"}
        assert answer == "Here is the kubernetes doc"

    def test_invalid_json_lines_skipped(self):
        lines = [
            "not valid json",
            "{broken",
            json.dumps({"type": "result", "result": "ok"}),
        ]
        tool_calls, answer = parse_stream_json("\n".join(lines))
        assert tool_calls == []
        assert answer == "ok"

    def test_mcp_prefixed_tool_name_normalized(self):
        lines = [
            json.dumps(
                {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {
                                "type": "tool_use",
                                "id": "tu_1",
                                "name": "mcp__folio__list_topics",
                                "input": {},
                            }
                        ]
                    },
                }
            ),
            json.dumps({"type": "result", "result": "done"}),
        ]
        tool_calls, _ = parse_stream_json("\n".join(lines))
        assert tool_calls[0].tool == "list_topics"

    def test_non_mcp_tool_name_unchanged(self):
        lines = [
            json.dumps(
                {
                    "type": "assistant",
                    "message": {
                        "content": [{"type": "tool_use", "id": "tu_1", "name": "Read", "input": {}}]
                    },
                }
            ),
            json.dumps({"type": "result", "result": "done"}),
        ]
        tool_calls, _ = parse_stream_json("\n".join(lines))
        assert tool_calls[0].tool == "Read"

    def test_tool_event_without_matching_assistant_ignored(self):
        lines = [
            json.dumps({"type": "tool", "id": "tu_orphan", "output": "some result"}),
            json.dumps({"type": "result", "result": "done"}),
        ]
        tool_calls, answer = parse_stream_json("\n".join(lines))
        assert tool_calls == []
        assert answer == "done"


class TestBuildMcpConfig:
    def test_multi_word_command_splits_into_command_and_args(self):
        config = _build_mcp_config("uv run folio-mcp", Path("/project"))
        server = config["mcpServers"]["folio"]
        assert server["command"] == "uv"
        assert server["args"] == ["run", "folio-mcp"]
        assert server["cwd"] == "/project"

    def test_single_word_command_has_empty_args(self):
        config = _build_mcp_config("folio-mcp", Path("/my/project"))
        server = config["mcpServers"]["folio"]
        assert server["command"] == "folio-mcp"
        assert server["args"] == []
        assert server["cwd"] == "/my/project"
