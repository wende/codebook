"""Tests for the CodeBook parser module."""

import pytest

from codebook.parser import CodeBookLink, CodeBookParser


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
            full_match="[``](codebook:server.test.empty)",
            value="",
            template="server.test.empty",
            start=0,
            end=32,
        )

        result = link.render("new value")

        assert result == "[`new value`](codebook:server.test.empty)"

    def test_render_handles_special_characters(self):
        """Render should handle special characters in value."""
        link = CodeBookLink(
            full_match="[`old`](codebook:server.test)",
            value="old",
            template="server.test",
            start=0,
            end=29,
        )

        result = link.render("hello <world> & stuff")

        assert result == "[`hello <world> & stuff`](codebook:server.test)"


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
        content = "Start [`42`](codebook:server.test) end"

        links = list(parser.find_links(content))

        assert len(links) == 1
        assert content[links[0].start : links[0].end] == links[0].full_match

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
        [`codebook`](codebook:server.test)
        [Another](http://test.com)
        """

        links = list(parser.find_links(content))

        assert len(links) == 1
        assert links[0].template == "server.test"

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
        [`13`](codebook:server.test)
        [`14`](codebook:server.test)
        [`15`](codebook:server.other)
        """

        templates = parser.find_templates(content)

        assert templates == ["server.test", "server.other"]

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
        content = "Some [`value`](codebook:server.test) here"

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
- Item 1: [`value`](codebook:server.test)
- Item 2: regular text
"""

        links = list(parser.find_links(content))

        assert len(links) == 1


class TestIncompleteTagDetection:
    """Tests for incomplete tag detection (mid-edit protection)."""

    @pytest.fixture
    def parser(self) -> CodeBookParser:
        """Create a parser instance."""
        return CodeBookParser()

    # Cicada tag tests
    def test_incomplete_cicada_missing_closing_bracket(self, parser: CodeBookParser):
        """Should detect cicada tag with missing > at end of file."""
        content = '<cicada endpoint="search-function" function_name="render"'
        assert parser.has_incomplete_tags(content) is True

    def test_incomplete_cicada_missing_closing_tag(self, parser: CodeBookParser):
        """Should detect cicada tag without </cicada>."""
        content = '<cicada endpoint="search-function">\nsome content'
        assert parser.has_incomplete_tags(content) is True

    def test_incomplete_cicada_unclosed_quote(self, parser: CodeBookParser):
        """Should detect cicada tag with unclosed quote."""
        content = '<cicada endpoint="search-function function_name="render">\nresult\n</cicada>'
        assert parser.has_incomplete_tags(content) is True

    def test_complete_cicada_tag(self, parser: CodeBookParser):
        """Should not flag complete cicada tags."""
        content = '<cicada endpoint="search-function" function_name="render">\nresult\n</cicada>'
        assert parser.has_incomplete_tags(content) is False

    # Exec tag tests
    def test_incomplete_exec_missing_closing_bracket(self, parser: CodeBookParser):
        """Should detect exec tag with missing >."""
        content = '<exec lang="python"'
        assert parser.has_incomplete_tags(content) is True

    def test_incomplete_exec_missing_closing_tag(self, parser: CodeBookParser):
        """Should detect exec tag without </exec>."""
        content = '<exec lang="python">\nprint("hello")'
        assert parser.has_incomplete_tags(content) is True

    def test_complete_exec_tag(self, parser: CodeBookParser):
        """Should not flag complete exec tags."""
        content = '<exec lang="python">\nprint("hello")\n</exec>\n<output>\nhello\n</output>'
        assert parser.has_incomplete_tags(content) is False

    # Div tag tests
    def test_incomplete_div_missing_closing_bracket(self, parser: CodeBookParser):
        """Should detect div tag with missing >."""
        content = '<div data-codebook="template"'
        assert parser.has_incomplete_tags(content) is True

    def test_incomplete_div_missing_closing_tag(self, parser: CodeBookParser):
        """Should detect div tag without </div>."""
        content = '<div data-codebook="template">\ncontent'
        assert parser.has_incomplete_tags(content) is True

    def test_complete_div_tag(self, parser: CodeBookParser):
        """Should not flag complete div tags."""
        content = '<div data-codebook="template">\ncontent\n</div>'
        assert parser.has_incomplete_tags(content) is False

    # Span tag tests
    def test_incomplete_span_missing_closing_bracket(self, parser: CodeBookParser):
        """Should detect span tag with missing >."""
        content = '<span data-codebook="template"'
        assert parser.has_incomplete_tags(content) is True

    def test_incomplete_span_missing_closing_tag(self, parser: CodeBookParser):
        """Should detect span tag without </span>."""
        content = '<span data-codebook="template">value'
        assert parser.has_incomplete_tags(content) is True

    def test_complete_span_tag(self, parser: CodeBookParser):
        """Should not flag complete span tags."""
        content = '<span data-codebook="template">value</span>'
        assert parser.has_incomplete_tags(content) is False

    # Mixed content tests
    def test_content_with_no_tags(self, parser: CodeBookParser):
        """Should not flag content with no special tags."""
        content = "Just regular markdown with [`value`](codebook:server.test)"
        assert parser.has_incomplete_tags(content) is False

    def test_mixed_complete_tags(self, parser: CodeBookParser):
        """Should not flag content with multiple complete tags."""
        content = """
# Documentation

<span data-codebook="count">42</span>

<div data-codebook="list">
- item 1
- item 2
</div>

<cicada endpoint="query" query="test">
results here
</cicada>
"""
        assert parser.has_incomplete_tags(content) is False

    def test_one_incomplete_among_complete(self, parser: CodeBookParser):
        """Should detect incomplete tag even when other tags are complete."""
        content = """
<span data-codebook="count">42</span>

<cicada endpoint="query
"""
        assert parser.has_incomplete_tags(content) is True


class TestMarkdownLinks:
    """Tests for markdown link detection (bidirectional links)."""

    @pytest.fixture
    def parser(self) -> CodeBookParser:
        """Create a parser instance."""
        return CodeBookParser()

    def test_find_markdown_links_to_md_files(self, parser: CodeBookParser):
        """Should find links to .md files."""
        from codebook.parser import LinkType

        content = "[Link Text](other-file.md)"

        links = list(parser.find_links(content))

        assert len(links) == 1
        assert links[0].link_type == LinkType.MARKDOWN_LINK
        assert links[0].value == "other-file.md"
        assert links[0].extra == "Link Text"

    def test_find_markdown_links_with_relative_path(self, parser: CodeBookParser):
        """Should find links with relative paths."""
        from codebook.parser import LinkType

        content = "[Documentation](./docs/README.md)"

        links = list(parser.find_links(content))

        assert len(links) == 1
        assert links[0].link_type == LinkType.MARKDOWN_LINK
        assert links[0].value == "./docs/README.md"

    def test_find_markdown_links_with_parent_path(self, parser: CodeBookParser):
        """Should find links with parent directory paths."""
        from codebook.parser import LinkType

        content = "[Parent Doc](../other/file.md)"

        links = list(parser.find_links(content))

        assert len(links) == 1
        assert links[0].link_type == LinkType.MARKDOWN_LINK
        assert links[0].value == "../other/file.md"

    def test_ignore_non_md_links(self, parser: CodeBookParser):
        """Should not match links to non-.md files."""
        content = """
[Website](https://example.com)
[Image](./image.png)
[Script](./script.py)
"""

        links = list(parser.find_links(content))

        # Should not find any MARKDOWN_LINK types
        from codebook.parser import LinkType
        md_links = [l for l in links if l.link_type == LinkType.MARKDOWN_LINK]
        assert len(md_links) == 0

    def test_find_multiple_markdown_links(self, parser: CodeBookParser):
        """Should find multiple markdown links in content."""
        from codebook.parser import LinkType

        content = """
See [introduction](intro.md) for getting started.
Also check [advanced topics](advanced.md) for more.
"""

        links = list(parser.find_links(content))
        md_links = [l for l in links if l.link_type == LinkType.MARKDOWN_LINK]

        assert len(md_links) == 2
        assert md_links[0].value == "intro.md"
        assert md_links[1].value == "advanced.md"

    def test_has_codebook_links_includes_markdown_links(self, parser: CodeBookParser):
        """has_codebook_links should return True for markdown links."""
        content = "[Doc](other.md)"

        assert parser.has_codebook_links(content) is True


class TestBacklinks:
    """Tests for backlink parsing."""

    @pytest.fixture
    def parser(self) -> CodeBookParser:
        """Create a parser instance."""
        return CodeBookParser()

    def test_find_backlinks(self, parser: CodeBookParser):
        """Should find backlinks with codebook:backlink attribute."""
        from codebook.parser import LinkType

        content = '[Link Text](source.md "codebook:backlink")'

        links = list(parser.find_links(content))

        assert len(links) == 1
        assert links[0].link_type == LinkType.BACKLINK
        assert links[0].value == "source.md"
        assert links[0].extra == "Link Text"

    def test_backlinks_in_section(self, parser: CodeBookParser):
        """Should find backlinks in a BACKLINKS section."""
        from codebook.parser import LinkType

        content = """
# Document

Some content here.

--- BACKLINKS ---
[Related Doc](related.md "codebook:backlink")
[Another Doc](another.md "codebook:backlink")
"""

        links = list(parser.find_links(content))
        backlinks = [l for l in links if l.link_type == LinkType.BACKLINK]

        assert len(backlinks) == 2
        assert backlinks[0].value == "related.md"
        assert backlinks[1].value == "another.md"

    def test_render_markdown_link(self, parser: CodeBookParser):
        """Should render markdown links correctly."""
        from codebook.parser import CodeBookLink, LinkType

        link = CodeBookLink(
            full_match="[Text](file.md)",
            value="file.md",
            template="",
            start=0,
            end=15,
            link_type=LinkType.MARKDOWN_LINK,
            extra="Text",
        )

        result = link.render("new-file.md")

        assert result == "[Text](new-file.md)"

    def test_render_backlink(self, parser: CodeBookParser):
        """Should render backlinks correctly."""
        from codebook.parser import CodeBookLink, LinkType

        link = CodeBookLink(
            full_match='[Text](file.md "codebook:backlink")',
            value="file.md",
            template="backlink",
            start=0,
            end=35,
            link_type=LinkType.BACKLINK,
            extra="Text",
        )

        result = link.render("new-file.md")

        assert result == '[Text](new-file.md "codebook:backlink")'


class TestFrontmatter:
    """Tests for frontmatter parsing."""

    @pytest.fixture
    def parser(self) -> CodeBookParser:
        """Create a parser instance."""
        return CodeBookParser()

    def test_parse_frontmatter_with_title(self, parser: CodeBookParser):
        """Should parse frontmatter with title."""
        content = """---
title: My Document
---

# Content here
"""
        frontmatter, body = parser.parse_frontmatter(content)

        assert frontmatter.title == "My Document"
        assert body.strip() == "# Content here"

    def test_parse_frontmatter_with_tags(self, parser: CodeBookParser):
        """Should parse frontmatter with tags array."""
        content = """---
tags: [api, documentation]
---

Content
"""
        frontmatter, body = parser.parse_frontmatter(content)

        assert frontmatter.tags == ["api", "documentation"]

    def test_parse_frontmatter_with_disable(self, parser: CodeBookParser):
        """Should parse frontmatter with disable array."""
        content = """---
disable: [links, backlinks]
---

Content
"""
        frontmatter, body = parser.parse_frontmatter(content)

        assert frontmatter.disable == ["links", "backlinks"]
        assert frontmatter.links_disabled is True
        assert frontmatter.backlinks_disabled is True

    def test_parse_frontmatter_links_disabled_property(self, parser: CodeBookParser):
        """Should correctly report links_disabled property."""
        content = """---
disable: [links]
---
"""
        frontmatter, _ = parser.parse_frontmatter(content)

        assert frontmatter.links_disabled is True
        assert frontmatter.backlinks_disabled is False

    def test_parse_frontmatter_backlinks_disabled_property(self, parser: CodeBookParser):
        """Should correctly report backlinks_disabled property."""
        content = """---
disable: [backlinks]
---
"""
        frontmatter, _ = parser.parse_frontmatter(content)

        assert frontmatter.links_disabled is False
        assert frontmatter.backlinks_disabled is True

    def test_parse_frontmatter_no_frontmatter(self, parser: CodeBookParser):
        """Should return empty frontmatter when none exists."""
        content = "# Just a heading\n\nSome content."

        frontmatter, body = parser.parse_frontmatter(content)

        assert frontmatter.title is None
        assert frontmatter.tags == []
        assert frontmatter.disable == []
        assert body == content

    def test_parse_frontmatter_preserves_raw(self, parser: CodeBookParser):
        """Should preserve raw frontmatter data."""
        content = """---
title: Test
custom_field: custom_value
---
"""
        frontmatter, _ = parser.parse_frontmatter(content)

        assert frontmatter.raw["title"] == "Test"
        assert frontmatter.raw["custom_field"] == "custom_value"

    def test_parse_frontmatter_invalid_yaml(self, parser: CodeBookParser):
        """Should return empty frontmatter for invalid YAML."""
        content = """---
title: [invalid yaml
  - missing bracket
---

Content
"""
        frontmatter, body = parser.parse_frontmatter(content)

        # Should return empty frontmatter and original content
        assert frontmatter.title is None
        assert body == content

    def test_parse_frontmatter_not_at_start(self, parser: CodeBookParser):
        """Should not parse frontmatter if not at document start."""
        content = """Some text first

---
title: Not Frontmatter
---
"""
        frontmatter, body = parser.parse_frontmatter(content)

        assert frontmatter.title is None
        assert body == content

    def test_parse_frontmatter_single_tag_as_string(self, parser: CodeBookParser):
        """Should handle single tag as string."""
        content = """---
tags: single-tag
---
"""
        frontmatter, _ = parser.parse_frontmatter(content)

        assert frontmatter.tags == ["single-tag"]

    def test_parse_frontmatter_single_disable_as_string(self, parser: CodeBookParser):
        """Should handle single disable as string."""
        content = """---
disable: links
---
"""
        frontmatter, _ = parser.parse_frontmatter(content)

        assert frontmatter.disable == ["links"]
        assert frontmatter.links_disabled is True

    def test_parse_frontmatter_complete_example(self, parser: CodeBookParser):
        """Should parse complete frontmatter example from spec."""
        content = """---
title: My Title
tags: [tag1, tag2]
disable: [links, backlinks]
---

# Document Content

Some text here.
"""
        frontmatter, body = parser.parse_frontmatter(content)

        assert frontmatter.title == "My Title"
        assert frontmatter.tags == ["tag1", "tag2"]
        assert frontmatter.disable == ["links", "backlinks"]
        assert frontmatter.links_disabled is True
        assert frontmatter.backlinks_disabled is True
        assert "# Document Content" in body
