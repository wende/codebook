"""Tests for Cicada module."""


from codebook.cicada import format_json_value, jq_query


class TestJqQuery:
    """Tests for jq_query function."""

    def test_simple_key_access(self):
        """Test accessing a simple key."""
        data = {"name": "test", "count": 42}
        assert jq_query(data, ".name") == "test"
        assert jq_query(data, ".count") == 42

    def test_nested_key_access(self):
        """Test accessing nested keys."""
        data = {"user": {"name": "alice", "age": 30}}
        assert jq_query(data, ".user.name") == "alice"
        assert jq_query(data, ".user.age") == 30

    def test_array_index_access(self):
        """Test accessing array elements by index."""
        data = {"items": ["a", "b", "c"]}
        assert jq_query(data, ".items[0]") == "a"
        assert jq_query(data, ".items[2]") == "c"

    def test_array_iterate_access(self):
        """Test accessing all array elements with []."""
        data = {"results": [{"x": 1}, {"x": 2}, {"x": 3}]}
        assert jq_query(data, ".results[].x") == [1, 2, 3]

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
        assert jq_query(data, ".response.data.users[0].name") == "alice"
        assert jq_query(data, ".response.data.users[].id") == [1, 2]

    def test_empty_path_returns_data(self):
        """Test that empty path returns original data."""
        data = {"key": "value"}
        assert jq_query(data, "") == data
        assert jq_query(data, ".") == data

    def test_missing_key_returns_none(self):
        """Test missing key returns None."""
        data = {"name": "test"}
        assert jq_query(data, ".missing") is None

    def test_out_of_bounds_index_returns_none(self):
        """Test out of bounds array index returns None."""
        data = {"items": ["a", "b"]}
        assert jq_query(data, ".items[5]") is None

    def test_invalid_query_returns_none(self):
        """Test invalid jq query returns None."""
        data = {"value": 42}
        assert jq_query(data, "invalid[[[") is None

    def test_multiple_selections_with_comma(self):
        """Test selecting multiple fields with comma operator."""
        data = {"module": "MyApp.User", "location": "lib/user.ex", "line": 42}
        result = jq_query(data, ".module,.location")
        assert result == ["MyApp.User", "lib/user.ex"]

    def test_multiple_selections_three_fields(self):
        """Test selecting three fields with comma operator."""
        data = {"a": 1, "b": 2, "c": 3}
        result = jq_query(data, ".a,.b,.c")
        assert result == [1, 2, 3]

    def test_select_filter(self):
        """Test jq select filter."""
        data = {"items": [{"x": 1}, {"x": 5}, {"x": 3}]}
        result = jq_query(data, ".items[] | select(.x > 2)")
        assert result == [{"x": 5}, {"x": 3}]

    def test_map_operation(self):
        """Test jq map operation."""
        data = {"numbers": [1, 2, 3]}
        result = jq_query(data, ".numbers | map(. * 2)")
        assert result == [2, 4, 6]

    def test_keys_operation(self):
        """Test jq keys operation."""
        data = {"a": 1, "b": 2, "c": 3}
        result = jq_query(data, "keys")
        assert result == ["a", "b", "c"]

    def test_length_operation(self):
        """Test jq length operation."""
        data = {"items": [1, 2, 3, 4, 5]}
        result = jq_query(data, ".items | length")
        assert result == 5

    def test_object_construction(self):
        """Test constructing new objects."""
        data = {"first_name": "John", "last_name": "Doe", "age": 30}
        result = jq_query(data, "{name: .first_name, years: .age}")
        assert result == {"name": "John", "years": 30}


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

    def test_format_list_of_strings_joins_with_line_breaks(self):
        """Test list of strings is joined with markdown line breaks."""
        assert format_json_value(["a", "b", "c"]) == "a  \nb  \nc"

    def test_format_list_of_mixed_returns_json(self):
        """Test list of mixed types is formatted as JSON."""
        assert format_json_value([1, 2, 3]) == "[\n  1,\n  2,\n  3\n]"
