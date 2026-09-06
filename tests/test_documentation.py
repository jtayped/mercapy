from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_FILES = tuple(sorted(ROOT.glob("*.md"))) + tuple(
    sorted((ROOT / "docs").rglob("*.md"))
)
FENCED_BLOCK = re.compile(r"^```.*?^```$", re.MULTILINE | re.DOTALL)
PYTHON_BLOCK = re.compile(r"^```python\n(.*?)^```$", re.MULTILINE | re.DOTALL)
INLINE_CODE = re.compile(r"`[^`]*`")
LINK_DESTINATION = re.compile(r"\]\([^)]*\)")
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")
HTML_TAG = re.compile(r"<[^>]*>")


def relative_name(path: Path) -> str:
    return str(path.relative_to(ROOT))


@pytest.mark.parametrize("path", MARKDOWN_FILES, ids=relative_name)
def test_documentation_prose_is_lowercase(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    prose = FENCED_BLOCK.sub("", source)
    prose = INLINE_CODE.sub("", prose)
    prose = LINK_DESTINATION.sub("]", prose)
    prose = HTML_TAG.sub("", prose)
    violations = [
        f"{relative_name(path)}:{line_number}: {line}"
        for line_number, line in enumerate(prose.splitlines(), start=1)
        if re.search(r"[A-Z]", line)
    ]
    assert not violations, "uppercase documentation prose:\n" + "\n".join(violations)


@pytest.mark.parametrize("path", MARKDOWN_FILES, ids=relative_name)
def test_local_documentation_links_resolve(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    for target in MARKDOWN_LINK.findall(source):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        relative_path, _, fragment = target.partition("#")
        destination = (path.parent / relative_path).resolve()
        assert destination.exists(), f"{relative_name(path)}: missing {target}"
        if not fragment or not destination.is_file():
            continue
        headings = destination.read_text(encoding="utf-8")
        anchors = {
            re.sub(r"[^a-z0-9 -]", "", heading.lower()).strip().replace(" ", "-")
            for heading in re.findall(r"^#{1,6} +(.*)$", headings, re.MULTILINE)
        }
        assert fragment in anchors, f"{relative_name(path)}: missing anchor {target}"


@pytest.mark.parametrize("path", MARKDOWN_FILES, ids=relative_name)
def test_python_documentation_blocks_compile(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    for block_number, code in enumerate(PYTHON_BLOCK.findall(source), start=1):
        compile(
            code,
            f"{relative_name(path)}:python-block-{block_number}",
            "exec",
        )
