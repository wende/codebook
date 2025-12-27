"""Tests for the CodeBook parser module."""

import pytest

from codebook.parser import CodeBookParser, CodeBookLink


class TestCodeBookLink:
    """Tests for CodeBookLink dataclass."""

    def test_render_generates_correct_link(self):
        """Render should produce valid markdown link with new value."""
        link = CodeBookLink(
            full_match="[`13`](codebook:SCIP.language_count)",
            value="13",
            template="SCIP.language_count",
            start=0,
            end=39,
        )

        result = link.render("15")

        assert result == "[`15`](codebook:SCIP.language_count)"

    def test_render_handles_empty_value(self):
        """Render should handle empty string value."""
        link = CodeBookLink(
            full_match="[``](codebook:test.empty)",
            value="",
            template="test.empty",
            start=0,
            end=25,
        )

        result = link.render("new value")

        assert result == "[`new value`](codebook:test.empty)"

    def test_render_handles_special_characters(self):
        """Render should handle special characters in value."""
        link = CodeBookLink(
            full_match="[`old`](codebook:test)",
            value="old",
            template="test",
            start=0,
            end=22,
        )

        result = link.render("hello <world> & stuff")

        assert result == "[`hello <world> & stuff`](codebook:test)"


class TestCodeBookParser:
    """Tests for CodeBookParser class."""

    @pytest.fixture
    def parser(self) -> CodeBookParser:
        """Create a parser instance."""
        return CodeBookParser()

    def test_find_links_extracts_all_links(self, parser: CodeBookParser):
        """Find links should extract all codebook links from content."""
        content = """
        CICADA supports [`13`](codebook:SCIP.language_count) languages.
        We have [`1000`](codebook:metrics.files) files indexed.
        """

        links = list(parser.find_links(content))

        assert len(links) == 2
        assert links[0].value == "13"
        assert links[0].template == "SCIP.language_count"
        assert links[1].value == "1000"
        assert links[1].template == "metrics.files"

    def test_find_links_returns_correct_positions(self, parser: CodeBookParser):
        """Links should have correct start/end positions."""
        content = "Start [`42`](codebook:test) end"

        links = list(parser.find_links(content))

        assert len(links) == 1
        assert links[0].start == 6
        assert links[0].end == 27
        assert content[links[0].start : links[0].end] == "[`42`](codebook:test)"

    def test_find_links_handles_empty_value(self, parser: CodeBookParser):
        """Should handle links with empty values."""
        content = "[``](codebook:empty.template)"

        links = list(parser.find_links(content))

        assert len(links) == 1
        assert links[0].value == ""
        assert links[0].template == "empty.template"

    def test_find_links_ignores_regular_links(self, parser: CodeBookParser):
        """Should ignore regular markdown links."""
        content = """
        [Regular link](https://example.com)
        [`codebook`](codebook:test)
        [Another](http://test.com)
        """

        links = list(parser.find_links(content))

        assert len(links) == 1
        assert links[0].template == "test"

    def test_find_links_handles_no_links(self, parser: CodeBookParser):
        """Should return empty iterator when no links found."""
        content = "Just regular markdown content."

        links = list(parser.find_links(content))

        assert len(links) == 0

    def test_find_links_handles_complex_templates(self, parser: CodeBookParser):
        """Should handle templates with dots and underscores."""
        content = "[`value`](codebook:module.sub_module.metric_name)"

        links = list(parser.find_links(content))

        assert len(links) == 1
        assert links[0].template == "module.sub_module.metric_name"

    def test_find_templates_extracts_unique_templates(self, parser: CodeBookParser):
        """Should extract unique template expressions."""
        content = """
        [`13`](codebook:test)
        [`14`](codebook:test)
        [`15`](codebook:other)
        """

        templates = parser.find_templates(content)

        assert templates == ["test", "other"]

    def test_find_templates_preserves_order(self, parser: CodeBookParser):
        """Should preserve order of first occurrence."""
        content = """
        [`a`](codebook:first)
        [`b`](codebook:second)
        [`c`](codebook:first)
        [`d`](codebook:third)
        """

        templates = parser.find_templates(content)

        assert templates == ["first", "second", "third"]

    def test_replace_values_updates_links(self, parser: CodeBookParser):
        """Should replace values in links with provided values."""
        content = "Count: [`13`](codebook:count)"

        result = parser.replace_values(content, {"count": "42"})

        assert result == "Count: [`42`](codebook:count)"

    def test_replace_values_handles_multiple_links(self, parser: CodeBookParser):
        """Should replace all matching links."""
        content = """
        [`a`](codebook:first)
        [`b`](codebook:second)
        """

        result = parser.replace_values(
            content,
            {
                "first": "X",
                "second": "Y",
            },
        )

        assert "[`X`](codebook:first)" in result
        assert "[`Y`](codebook:second)" in result

    def test_replace_values_preserves_unknown_templates(self, parser: CodeBookParser):
        """Should keep original value if template not in values dict."""
        content = "[`old`](codebook:unknown)"

        result = parser.replace_values(content, {"other": "value"})

        assert result == "[`old`](codebook:unknown)"

    def test_replace_values_handles_same_template_multiple_times(
        self,
        parser: CodeBookParser,
    ):
        """Should replace all occurrences of the same template."""
        content = """
        First: [`a`](codebook:count)
        Second: [`b`](codebook:count)
        """

        result = parser.replace_values(content, {"count": "42"})

        assert result.count("[`42`](codebook:count)") == 2

    def test_has_codebook_links_returns_true_when_present(
        self,
        parser: CodeBookParser,
    ):
        """Should return True when codebook links exist."""
        content = "Some [`value`](codebook:test) here"

        assert parser.has_codebook_links(content) is True

    def test_has_codebook_links_returns_false_when_absent(
        self,
        parser: CodeBookParser,
    ):
        """Should return False when no codebook links exist."""
        content = "Regular [link](https://example.com)"

        assert parser.has_codebook_links(content) is False

    def test_count_links_returns_correct_count(self, parser: CodeBookParser):
        """Should return correct number of links."""
        content = """
        [`a`](codebook:one)
        [`b`](codebook:two)
        [`c`](codebook:three)
        """

        assert parser.count_links(content) == 3

    def test_count_links_returns_zero_for_no_links(self, parser: CodeBookParser):
        """Should return zero when no links present."""
        content = "No links here"

        assert parser.count_links(content) == 0

    def test_multiline_content_handling(self, parser: CodeBookParser):
        """Should handle content spanning multiple lines correctly."""
        content = """# Title

First paragraph with [`value1`](codebook:template1).

Second paragraph.

Third paragraph with [`value2`](codebook:template2).
"""

        links = list(parser.find_links(content))

        assert len(links) == 2
        assert links[0].template == "template1"
        assert links[1].template == "template2"

    def test_adjacent_links(self, parser: CodeBookParser):
        """Should handle adjacent links without space."""
        content = "[`a`](codebook:first)[`b`](codebook:second)"

        links = list(parser.find_links(content))

        assert len(links) == 2

    def test_link_in_list_item(self, parser: CodeBookParser):
        """Should find links in list items."""
        content = """
- Item 1: [`value`](codebook:test)
- Item 2: regular text
"""

        links = list(parser.find_links(content))

        assert len(links) == 1
