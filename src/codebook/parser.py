"""Link parser for CodeBook markdown files.

This module handles parsing and manipulation of codebook links in markdown files.

Supported formats:
1. Inline link: [`VALUE`](codebook:TEMPLATE) or [VALUE](codebook:TEMPLATE)
2. URL link: [text](URL "codebook:TEMPLATE") - resolves to update the URL
3. Span: <span data-codebook="TEMPLATE">VALUE</span>
4. Div: <div data-codebook="TEMPLATE">MULTILINE</div>
5. Exec: <exec lang="python">CODE</exec><output>RESULT</output> - executable code
6. Cicada: <cicada endpoint="..." params...>RESULT</cicada> - Cicada API queries
"""

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator


class LinkType(Enum):
    """Types of codebook links supported."""

    INLINE = "inline"  # [`VALUE`](codebook:TEMPLATE)
    URL = "url"  # [text](URL "codebook:TEMPLATE")
    MARKDOWN_LINK = "markdown_link"  # [text](file.md) - standard markdown link
    BACKLINK = "backlink"  # [text](URL "codebook:backlink") - auto-generated backlink
    SPAN = "span"  # <span data-codebook="TEMPLATE">VALUE</span>
    DIV = "div"  # <div data-codebook="TEMPLATE">CONTENT</div>
    EXEC = "exec"  # <exec lang="python">CODE</exec><output>RESULT</output>
    CICADA = "cicada"  # <cicada endpoint="...">RESULT</cicada>


@dataclass
class CodeBookLink:
    """Represents a codebook link found in markdown.

    Attributes:
        full_match: The complete matched string
        value: The current value (displayed text, URL, or content)
        template: The template expression to resolve
        start: Start position of the match in the source text
        end: End position of the match in the source text
        link_type: The type of link (inline, url, span, div)
        extra: Additional data (e.g., link text for URL type)
        params: Additional parameters (e.g., for Cicada queries)
    """

    full_match: str
    value: str
    template: str
    start: int
    end: int
    link_type: LinkType = LinkType.INLINE
    extra: str | None = None
    params: dict[str, str] = field(default_factory=dict)

    def render(self, new_value: str) -> str:
        """Generate the link with a new value.

        Args:
            new_value: The new value to display/use

        Returns:
            The formatted link with the new value
        """
        if self.link_type == LinkType.INLINE:
            return f"[`{new_value}`](codebook:{self.template})"
        elif self.link_type == LinkType.URL:
            # extra contains the link text
            return f'[{self.extra}]({new_value} "codebook:{self.template}")'
        elif self.link_type == LinkType.MARKDOWN_LINK:
            # extra contains the link text, value is the URL
            return f"[{self.extra}]({new_value})"
        elif self.link_type == LinkType.BACKLINK:
            # extra contains the link text, value is the URL
            return f'[{self.extra}]({new_value} "codebook:backlink")'
        elif self.link_type == LinkType.SPAN:
            return f'<span data-codebook="{self.template}">{new_value}</span>'
        elif self.link_type == LinkType.DIV:
            return f'<div data-codebook="{self.template}">\n{new_value}\n</div>'
        elif self.link_type == LinkType.EXEC:
            # extra contains the language, template contains the code
            return f'<exec lang="{self.extra}">\n{self.template}\n</exec>\n<output>\n{new_value}\n</output>'
        elif self.link_type == LinkType.CICADA:
            # template contains the endpoint, params contains query parameters
            attrs = f'endpoint="{self.template}"'
            for key, val in self.params.items():
                attrs += f' {key}="{val}"'
            return f"<cicada {attrs}>\n{new_value}\n</cicada>"
        return self.full_match


class CodeBookParser:
    """Parser for extracting and manipulating codebook links in markdown.

    Supported formats:
    1. [`VALUE`](codebook:TEMPLATE) - inline value display
    2. [text](URL "codebook:TEMPLATE") - URL that gets updated
    3. <span data-codebook="TEMPLATE">VALUE</span> - inline HTML
    4. <div data-codebook="TEMPLATE">CONTENT</div> - multiline HTML
    """

    # Pattern 1: [`VALUE`](codebook:TEMPLATE) or [VALUE](codebook:TEMPLATE)
    INLINE_PATTERN = re.compile(r"\[`?([^`\]]*)`?\]\(codebook:([^)]+)\)")

    # Pattern 2: [text](URL "codebook:TEMPLATE") - excludes link/backlink
    URL_PATTERN = re.compile(r'\[([^\]]+)\]\(([^"\s]+)\s+"codebook:(?!link\b|backlink\b)([^"]+)"\)')

    # Pattern 2a: [text](file.md) - standard markdown link to .md files
    # Matches links to .md files without any title attribute
    MARKDOWN_LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^"\s)]+\.md)\)')

    # Pattern 2b: [text](URL "codebook:backlink") - backlink (auto-generated)
    BACKLINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^"\s]+)\s+"codebook:backlink"\)')

    # Pattern 3: <span data-codebook="TEMPLATE">VALUE</span>
    SPAN_PATTERN = re.compile(r'<span data-codebook="([^"]+)">([^<]*)</span>')

    # Pattern 4: <div data-codebook="TEMPLATE">CONTENT</div> (multiline)
    DIV_PATTERN = re.compile(
        r'<div data-codebook="([^"]+)">\n?(.*?)\n?</div>', re.DOTALL
    )

    # Pattern 5: <exec lang="LANG">CODE</exec>\n<output>RESULT</output>
    EXEC_PATTERN = re.compile(
        r'<exec lang="([^"]+)">\n?(.*?)\n?</exec>\s*\n<output>\n?(.*?)\n?</output>',
        re.DOTALL,
    )

    # Pattern 6: <cicada endpoint="..." attr="val">CONTENT</cicada>
    CICADA_PATTERN = re.compile(
        r'<cicada\s+([^>]+)>\n?(.*?)\n?</cicada>',
        re.DOTALL,
    )

    # Helper pattern to extract attributes from cicada tag
    ATTR_PATTERN = re.compile(r'(\w+)="([^"]*)"')

    def find_links(self, content: str) -> Iterator[CodeBookLink]:
        """Find all codebook links in the given content.

        Args:
            content: The markdown content to parse

        Yields:
            CodeBookLink objects for each link found
        """
        # Find inline links: [`VALUE`](codebook:TEMPLATE)
        for match in self.INLINE_PATTERN.finditer(content):
            yield CodeBookLink(
                full_match=match.group(0),
                value=match.group(1),
                template=match.group(2),
                start=match.start(),
                end=match.end(),
                link_type=LinkType.INLINE,
            )

        # Find URL links: [text](URL "codebook:TEMPLATE")
        for match in self.URL_PATTERN.finditer(content):
            yield CodeBookLink(
                full_match=match.group(0),
                value=match.group(2),  # URL is the value
                template=match.group(3),
                start=match.start(),
                end=match.end(),
                link_type=LinkType.URL,
                extra=match.group(1),  # link text
            )

        # Find standard markdown links to .md files: [text](file.md)
        for match in self.MARKDOWN_LINK_PATTERN.finditer(content):
            yield CodeBookLink(
                full_match=match.group(0),
                value=match.group(2),  # URL/path is the value
                template="",  # no template for standard links
                start=match.start(),
                end=match.end(),
                link_type=LinkType.MARKDOWN_LINK,
                extra=match.group(1),  # link text
            )

        # Find backlinks: [text](URL "codebook:backlink")
        for match in self.BACKLINK_PATTERN.finditer(content):
            yield CodeBookLink(
                full_match=match.group(0),
                value=match.group(2),  # URL is the value
                template="backlink",  # special template marker
                start=match.start(),
                end=match.end(),
                link_type=LinkType.BACKLINK,
                extra=match.group(1),  # link text
            )

        # Find span elements: <span data-codebook="TEMPLATE">VALUE</span>
        for match in self.SPAN_PATTERN.finditer(content):
            yield CodeBookLink(
                full_match=match.group(0),
                value=match.group(2),
                template=match.group(1),
                start=match.start(),
                end=match.end(),
                link_type=LinkType.SPAN,
            )

        # Find div elements: <div data-codebook="TEMPLATE">CONTENT</div>
        for match in self.DIV_PATTERN.finditer(content):
            yield CodeBookLink(
                full_match=match.group(0),
                value=match.group(2),
                template=match.group(1),
                start=match.start(),
                end=match.end(),
                link_type=LinkType.DIV,
            )

        # Find exec blocks: <exec lang="LANG">CODE</exec><output>RESULT</output>
        for match in self.EXEC_PATTERN.finditer(content):
            yield CodeBookLink(
                full_match=match.group(0),
                value=match.group(3),  # current output
                template=match.group(2),  # code to execute
                start=match.start(),
                end=match.end(),
                link_type=LinkType.EXEC,
                extra=match.group(1),  # language
            )

        # Find cicada blocks: <cicada endpoint="..." params...>CONTENT</cicada>
        for match in self.CICADA_PATTERN.finditer(content):
            attrs_str = match.group(1)
            content_value = match.group(2)

            # Parse attributes
            attrs = dict(self.ATTR_PATTERN.findall(attrs_str))
            endpoint = attrs.pop("endpoint", "query")

            yield CodeBookLink(
                full_match=match.group(0),
                value=content_value,
                template=endpoint,  # endpoint name
                start=match.start(),
                end=match.end(),
                link_type=LinkType.CICADA,
                params=attrs,  # remaining attributes as params
            )

    def find_templates(self, content: str) -> list[str]:
        """Extract all unique template expressions from content.

        Args:
            content: The markdown content to parse

        Returns:
            List of unique template expressions found (preserves order)
        """
        templates: list[str] = []
        seen: set[str] = set()
        for link in self.find_links(content):
            if link.template not in seen:
                templates.append(link.template)
                seen.add(link.template)
        return templates

    def replace_values(self, content: str, values: dict[str, str]) -> str:
        """Replace link values in content with resolved values.

        Args:
            content: The markdown content to update
            values: Mapping of template expressions to their resolved values

        Returns:
            Updated content with new values in links
        """
        # Process each pattern type separately

        # 1. Inline links
        def inline_replacer(match: re.Match[str]) -> str:
            template = match.group(2)
            if template in values:
                new_value = str(values[template])
                return f"[`{new_value}`](codebook:{template})"
            return match.group(0)

        content = self.INLINE_PATTERN.sub(inline_replacer, content)

        # 2. URL links
        def url_replacer(match: re.Match[str]) -> str:
            template = match.group(3)
            link_text = match.group(1)
            if template in values:
                new_url = str(values[template])
                return f'[{link_text}]({new_url} "codebook:{template}")'
            return match.group(0)

        content = self.URL_PATTERN.sub(url_replacer, content)

        # 3. Span elements
        def span_replacer(match: re.Match[str]) -> str:
            template = match.group(1)
            if template in values:
                new_value = str(values[template])
                return f'<span data-codebook="{template}">{new_value}</span>'
            return match.group(0)

        content = self.SPAN_PATTERN.sub(span_replacer, content)

        # 4. Div elements
        def div_replacer(match: re.Match[str]) -> str:
            template = match.group(1)
            if template in values:
                new_value = str(values[template])
                return f'<div data-codebook="{template}">\n{new_value}\n</div>'
            return match.group(0)

        content = self.DIV_PATTERN.sub(div_replacer, content)

        return content

    def has_codebook_links(self, content: str) -> bool:
        """Check if content contains any codebook links.

        Args:
            content: The markdown content to check

        Returns:
            True if at least one codebook link is found
        """
        return (
            self.INLINE_PATTERN.search(content) is not None
            or self.URL_PATTERN.search(content) is not None
            or self.MARKDOWN_LINK_PATTERN.search(content) is not None
            or self.BACKLINK_PATTERN.search(content) is not None
            or self.SPAN_PATTERN.search(content) is not None
            or self.DIV_PATTERN.search(content) is not None
            or self.EXEC_PATTERN.search(content) is not None
            or self.CICADA_PATTERN.search(content) is not None
        )

    def count_links(self, content: str) -> int:
        """Count the number of codebook links in content.

        Args:
            content: The markdown content to analyze

        Returns:
            Number of codebook links found
        """
        return len(list(self.find_links(content)))

    def has_incomplete_tags(self, content: str) -> bool:
        """Check if content contains incomplete (being edited) tags.

        This detects tags that are partially written, such as:
        - <cicada endpoint="search-function (missing closing >)
        - <cicada endpoint="search-function"> (missing </cicada>)
        - <exec lang="python (missing closing >)
        - <div data-codebook="template (missing closing >)
        - <span data-codebook="template (missing closing >)

        Args:
            content: The markdown content to check

        Returns:
            True if incomplete tags are detected
        """
        # Patterns for opening tags that might be incomplete
        incomplete_patterns = [
            # <cicada with attributes but no closing > before </cicada> or EOF
            (r'<cicada\s+[^>]*$', None),  # <cicada ... at end of content
            (r'<cicada\s+(?:[^>]*\n)+[^>]*$', None),  # <cicada ... multiline, no >
            # <cicada ...> without </cicada>
            (r'<cicada\s+[^>]+>', r'</cicada>'),
            # <exec with no closing >
            (r'<exec\s+[^>]*$', None),
            # <exec ...> without </exec>
            (r'<exec\s+[^>]+>', r'</exec>'),
            # <div data-codebook with no closing >
            (r'<div\s+data-codebook="[^"]*$', None),
            (r'<div\s+data-codebook="[^"]*"[^>]*$', None),
            # <div data-codebook=...> without </div>
            (r'<div\s+data-codebook="[^"]*"[^>]*>', r'</div>'),
            # <span data-codebook with no closing >
            (r'<span\s+data-codebook="[^"]*$', None),
            (r'<span\s+data-codebook="[^"]*"[^>]*$', None),
            # <span data-codebook=...> without </span>
            (r'<span\s+data-codebook="[^"]*"[^>]*>', r'</span>'),
        ]

        for open_pattern, close_tag in incomplete_patterns:
            matches = list(re.finditer(open_pattern, content, re.DOTALL))
            for match in matches:
                if close_tag is None:
                    # Pattern itself indicates incompleteness (no closing >)
                    return True
                else:
                    # Check if there's a closing tag after the opening
                    remaining = content[match.end():]
                    if close_tag not in remaining:
                        return True

        # Check for unclosed quotes in attribute values within tag openings
        # This catches <cicada endpoint="value  (missing closing quote)
        tag_starts = [
            (r'<cicada\s+', r'>'),
            (r'<exec\s+', r'>'),
            (r'<div\s+data-codebook=', r'>'),
            (r'<span\s+data-codebook=', r'>'),
        ]

        for start_pattern, end_char in tag_starts:
            for match in re.finditer(start_pattern, content):
                start_pos = match.end()
                # Find the closing > for this tag
                end_pos = content.find(end_char, start_pos)
                if end_pos == -1:
                    # No closing >, definitely incomplete
                    return True
                # Check for unbalanced quotes in the attributes
                attr_content = content[start_pos:end_pos]
                quote_count = attr_content.count('"')
                if quote_count % 2 != 0:
                    # Odd number of quotes means unclosed quote
                    return True

        return False
