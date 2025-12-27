"""Tests for Cicada module."""

import pytest

from codebook.cicada import jsonpath_get, format_json_value


class TestJsonPathGet:
    """Tests for jsonpath_get function."""

    def test_simple_key_access(self):
        """Test accessing a simple key."""
        data = {"name": "test", "count": 42}
        assert jsonpath_get(data, ".name") == "test"
        assert jsonpath_get(data, ".count") == 42

    def test_nested_key_access(self):
        """Test accessing nested keys."""
        data = {"user": {"name": "alice", "age": 30}}
        assert jsonpath_get(data, ".user.name") == "alice"
        assert jsonpath_get(data, ".user.age") == 30

    def test_array_index_access(self):
        """Test accessing array elements by index."""
        data = {"items": ["a", "b", "c"]}
        assert jsonpath_get(data, ".items[0]") == "a"
        assert jsonpath_get(data, ".items[2]") == "c"

    def test_array_wildcard_access(self):
        """Test accessing all array elements."""
        data = {"results": [{"x": 1}, {"x": 2}, {"x": 3}]}
        assert jsonpath_get(data, ".results[*].x") == [1, 2, 3]

    def test_complex_path(self):
        """Test complex nested paths."""
        data = {
            "response": {
                "data": {
                    "users": [
                        {"id": 1, "name": "alice"},
                        {"id": 2, "name": "bob"},
                    ]
                }
            }
        }
        assert jsonpath_get(data, ".response.data.users[0].name") == "alice"
        assert jsonpath_get(data, ".response.data.users[*].id") == [1, 2]

    def test_empty_path_returns_data(self):
        """Test that empty path returns original data."""
        data = {"key": "value"}
        assert jsonpath_get(data, "") == data
        assert jsonpath_get(data, ".") == data

    def test_path_without_leading_dot(self):
        """Test path without leading dot still works."""
        data = {"name": "test"}
        assert jsonpath_get(data, "name") == "test"

    def test_missing_key_returns_none(self):
        """Test missing key returns None."""
        data = {"name": "test"}
        assert jsonpath_get(data, ".missing") is None

    def test_out_of_bounds_index_returns_none(self):
        """Test out of bounds array index returns None."""
        data = {"items": ["a", "b"]}
        assert jsonpath_get(data, ".items[5]") is None

    def test_invalid_path_on_primitive_returns_none(self):
        """Test accessing key on primitive returns None."""
        data = {"value": 42}
        assert jsonpath_get(data, ".value.nested") is None


class TestFormatJsonValue:
    """Tests for format_json_value function."""

    def test_format_none_returns_empty(self):
        """Test None returns empty string."""
        assert format_json_value(None) == ""

    def test_format_string_returns_as_is(self):
        """Test string is returned as-is."""
        assert format_json_value("hello") == "hello"

    def test_format_number_returns_string(self):
        """Test numbers are converted to string."""
        assert format_json_value(42) == "42"
        assert format_json_value(3.14) == "3.14"

    def test_format_bool_returns_string(self):
        """Test booleans are converted to string."""
        assert format_json_value(True) == "True"
        assert format_json_value(False) == "False"

    def test_format_dict_returns_json(self):
        """Test dict is formatted as JSON."""
        assert format_json_value({"a": 1}) == '{\n  "a": 1\n}'

    def test_format_list_of_strings_joins_with_newlines(self):
        """Test list of strings is joined with double newlines."""
        assert format_json_value(["a", "b", "c"]) == "a\n\nb\n\nc"

    def test_format_list_of_mixed_returns_json(self):
        """Test list of mixed types is formatted as JSON."""
        assert format_json_value([1, 2, 3]) == "[\n  1,\n  2,\n  3\n]"
