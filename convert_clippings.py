#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path


HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
CONTENT_TAGS = {"p", "li", "blockquote", "pre", "div"}
HEADING_SEPARATOR = "--"


def sanitize_component(text: str) -> str:
    cleaned = re.sub(r"[^\w\s-]+", "", text).strip()
    dashed = re.sub(r"\s+", "-", cleaned)
    return dashed or "Untitled"


class BlockParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.blocks: list[tuple[str, str]] = []
        self._tag_stack: list[str] = []
        self._capture_tag: str | None = None
        self._buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._tag_stack.append(tag)
        if tag in HEADING_TAGS or tag in CONTENT_TAGS:
            self._capture_tag = tag
            self._buffer = []

    def handle_endtag(self, tag: str) -> None:
        if self._capture_tag == tag:
            stripped_parts = [part.strip() for part in self._buffer]
            text = " ".join(part for part in stripped_parts if part).strip()
            if text:
                self.blocks.append((tag, text))
            self._capture_tag = None
            self._buffer = []
        if self._tag_stack and self._tag_stack[-1] == tag:
            self._tag_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._capture_tag is not None:
            self._buffer.append(data)


@dataclass
class ClipDocument:
    heading: str
    subheading: str
    paragraphs: list[str] = field(default_factory=list)


def parse_documents(html_text: str) -> list[ClipDocument]:
    parser = BlockParser()
    parser.feed(html_text)

    docs: list[ClipDocument] = []
    current_heading: str | None = None
    current_doc: ClipDocument | None = None

    for tag, text in parser.blocks:
        if tag == "h1":
            current_heading = text
            current_doc = None
            continue
        if tag in {"h2", "h3", "h4", "h5", "h6"}:
            heading = current_heading or "General"
            current_doc = ClipDocument(heading=heading, subheading=text)
            docs.append(current_doc)
            continue
        if current_doc is not None:
            current_doc.paragraphs.append(text)

    return docs


def write_documents(documents: list[ClipDocument], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written_files: list[Path] = []
    filename_counts: dict[str, int] = {}

    for doc in documents:
        base_name = (
            f"{sanitize_component(doc.heading)}"
            f"{HEADING_SEPARATOR}"
            f"{sanitize_component(doc.subheading)}"
        )
        counter = filename_counts.get(base_name, 0)

        body = "\n\n".join(doc.paragraphs).strip()
        content = f"# {doc.heading}\n\n## {doc.subheading}\n"
        if body:
            content += f"\n{body}\n"
        else:
            content += "\n"

        while True:
            suffix = "" if counter == 0 else f"-{counter}"
            file_path = output_dir / f"{base_name}{suffix}.md"
            try:
                with file_path.open("x", encoding="utf-8") as f:
                    f.write(content)
                break
            except FileExistsError:
                counter += 1

        filename_counts[base_name] = counter + 1
        written_files.append(file_path)

    return written_files


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert clipping HTML export to one markdown file per subheading."
    )
    parser.add_argument("input_html", type=Path, help="Path to clippings.html export")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory where markdown files will be written (default: current directory)",
    )
    args = parser.parse_args()

    try:
        html_text = args.input_html.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        parser.error(
            f"Unable to decode input HTML file '{args.input_html}' as UTF-8: {exc}. "
            "Re-export or convert the file to UTF-8 encoding."
        )
    except OSError as exc:
        parser.error(
            f"Unable to read input HTML file '{args.input_html}': {exc}. "
            "Check that the file exists and is readable."
        )
    documents = parse_documents(html_text)
    written_files = write_documents(documents, args.output_dir)
    print(f"Wrote {len(written_files)} markdown files to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
