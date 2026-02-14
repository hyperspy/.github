import argparse
import os
import re


def extract_release_notes(changelog_path, heading_level=None):
    with open(changelog_path, encoding="utf-8") as f:
        content = f.read()

    ext = os.path.splitext(changelog_path)[1].lower()
    if ext == ".md":
        return _extract_markdown(content, heading_level=heading_level)
    else:
        return _extract_rst(content, adornment_char=heading_level)


def _extract_rst(content, adornment_char=None):
    """Extract the first section under the second-level RST heading.

    Parameters
    ----------
    content : str
        The RST file content.
    adornment_char : str or None
        If provided, use this character to identify the heading level to
        extract.  If ``None`` (default), heading levels are determined by
        order of appearance of the underline character and the second
        distinct adornment character is used.
    """
    # Match all RST section headings: a text line followed by a line of
    # repeated punctuation (with optional overline).
    heading_re = re.compile(
        r"^(?:([^\w\s])\1+\n)?"  # optional overline
        r".+\n"                   # title text
        r"([^\w\s])\2+$",        # underline (capture the character)
        re.MULTILINE,
    )

    # Discover heading level order by first appearance of each adornment char
    seen_chars = []
    for m in heading_re.finditer(content):
        char = m.group(2)
        if char not in seen_chars:
            seen_chars.append(char)
        if len(seen_chars) >= 2:
            break

    if adornment_char is not None:
        target_char = adornment_char
    elif len(seen_chars) >= 2:
        target_char = seen_chars[1]
    elif len(seen_chars) == 1:
        # Only one heading level – use it
        target_char = seen_chars[0]
    else:
        return ""

    level2_char = re.escape(target_char)
    section_re = re.compile(
        r"^(?:" + level2_char + r"+\n)?"  # optional overline
        r".+\n"
        r"" + level2_char + r"+$",
        re.MULTILINE,
    )

    matches = list(section_re.finditer(content))
    if not matches:
        return ""

    start = matches[0].end() + 1
    end = matches[1].start() if len(matches) > 1 else len(content)
    section = content[start:end].strip()
    return _rst_to_markdown(section, seen_chars)


def _rst_to_markdown(text, heading_chars):
    """Convert RST text to Markdown.

    Handles:
    - RST section headings → Markdown ``###`` headings
    - ``:ref:`text <target>``` → ``text``
    - ``:role:`~mod.name``` → ``name``
    - ``:role:`target``` → ``target``
    - RST inline literals ` `` `` ` → Markdown backtick `` ` ``
    - RST external links ```text <url>`_`` → ``[text](url)``
    - External links like ``(`#123 <url>`_)`` → ``([#123](url))``
    """
    # Convert RST section headings to Markdown headings.
    # heading_chars contains the adornment chars in order of appearance;
    # the extracted section is one level below the matched heading, so
    # sub-headings inside start from the next char onwards.
    heading_re = re.compile(
        r"^(?:([^\w\s])\1+\n)?"  # optional overline
        r"(.+)\n"                 # title text
        r"([^\w\s])\3+$",        # underline
        re.MULTILINE,
    )

    def _heading_repl(m):
        char = m.group(3)
        title = m.group(2).strip()
        try:
            depth = heading_chars.index(char) + 1
        except ValueError:
            depth = len(heading_chars) + 1
        prefix = "#" * depth
        return f"{prefix} {title}"

    text = heading_re.sub(_heading_repl, text)

    # :ref:`visible text <target>` → visible text
    text = re.sub(r":ref:`([^<`]+?)\s*<[^>]+>`", r"\1", text)

    # :role:`~mod.name` → `name`  (tilde shortens to last component)
    text = re.sub(r":\w+:`~[\w.]*\.(\w+)`", r"`\1`", text)

    # :role:`target` → `target`
    text = re.sub(r":\w+:`([^`]+)`", r"`\1`", text)

    # RST external links: `text <url>`_ → [text](url)
    text = re.sub(r"`([^<`]+?)\s*<([^>]+)>`_", r"[\1](\2)", text)

    # RST inline literals: ``code`` → `code`
    text = re.sub(r"``(.+?)``", r"`\1`", text)

    return text


def _extract_markdown(content, heading_level=None):
    """Extract the first section under a Markdown heading.

    Parameters
    ----------
    content : str
        The Markdown file content.
    heading_level : int or str or None
        Heading level to extract (e.g. ``2`` for ``##``).  If ``None``
        (default), the second distinct heading level found in the file
        is used.
    """
    heading_re = re.compile(r"^(#{1,6}) .+", re.MULTILINE)

    if heading_level is not None:
        level = int(heading_level)
    else:
        # Auto-detect: find the second distinct heading level
        seen_levels = []
        for m in heading_re.finditer(content):
            lvl = len(m.group(1))
            if lvl not in seen_levels:
                seen_levels.append(lvl)
            if len(seen_levels) >= 2:
                break

        if len(seen_levels) >= 2:
            level = seen_levels[1]
        elif len(seen_levels) == 1:
            level = seen_levels[0]
        else:
            return ""

    prefix = "#" * level
    section_re = re.compile(r"^" + re.escape(prefix) + r" .+", re.MULTILINE)
    matches = list(section_re.finditer(content))
    if not matches:
        return ""

    start = matches[0].end() + 1
    end = matches[1].start() if len(matches) > 1 else len(content)
    return content[start:end].strip()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract release notes from a changelog file.")
    parser.add_argument("changelog", help="Path to the changelog file")
    parser.add_argument(
        "--heading-level",
        default=None,
        help="Heading level to extract. For RST: the adornment character "
        "(e.g. '='). For Markdown: the heading depth as a number "
        "(e.g. '2' for '##'). If omitted, the second distinct heading "
        "level found in the file is used.",
    )
    parser.add_argument(
        "--output-name",
        default="release-notes",
        help="Name of the GitHub Actions output variable to set "
        "(default: 'release-notes').",
    )
    args = parser.parse_args()

    notes = extract_release_notes(args.changelog, heading_level=args.heading_level)

    # Write to GITHUB_OUTPUT if running in GitHub Actions, otherwise print
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            delimiter = "EOF_RELEASE_NOTES"
            f.write(f"{args.output_name}<<{delimiter}\n{notes}\n{delimiter}\n")
    else:
        print(notes)
