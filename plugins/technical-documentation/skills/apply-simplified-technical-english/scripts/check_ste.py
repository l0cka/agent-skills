#!/usr/bin/env python3
"""Check human-facing documentation for detectable ASD-STE100 issues.

This checker implements conservative structural heuristics. It does not replace
the ASD-STE100 controlled dictionary or a manual technical review.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import sys
from typing import Iterator, Sequence


TEXT_EXTENSIONS = {".adoc", ".md", ".mdx", ".rst", ".text", ".txt"}
EXCLUDED_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "build",
    "dist",
    "node_modules",
    "vendor",
    "venv",
}
PROCEDURAL_HEADINGS = re.compile(
    r"\b(?:configuration|deployment|getting started|installation|instructions|"
    r"operation|operations|procedure|procedures|quick start|runbook|setup|steps|"
    r"troubleshooting|usage)\b",
    re.IGNORECASE,
)
IMPERATIVE_VERBS = {
    "add", "apply", "attach", "check", "choose", "clean", "click", "close",
    "connect", "continue", "copy", "create", "delete", "disable", "disconnect",
    "download", "enable", "enter", "examine", "install", "keep", "make", "move",
    "open", "press", "put", "read", "record", "remove", "replace", "restart",
    "run", "save", "select", "set", "start", "stop", "type", "update", "upload",
    "use", "verify", "wait", "write",
}
CONTRACTIONS = re.compile(
    r"\b(?:aren't|can't|couldn't|didn't|doesn't|don't|hadn't|hasn't|haven't|"
    r"he's|here's|i'd|i'll|i'm|i've|isn't|it's|let's|mustn't|shan't|she's|"
    r"shouldn't|that's|there's|they'd|they'll|they're|they've|wasn't|we'd|"
    r"we'll|we're|we've|weren't|what's|where's|who's|won't|wouldn't|you'd|"
    r"you'll|you're|you've)\b",
    re.IGNORECASE,
)
PASSIVE_VOICE = re.compile(
    r"\b(?:am|are|be|been|being|is|was|were)\s+(?:\w+ly\s+)?"
    r"[A-Za-z]+(?:ed|en)\b",
    re.IGNORECASE,
)
BRITISH_SPELLINGS = re.compile(
    r"\b(?:behaviour|centre|colour|defence|fibre|licence|organise|organisation|"
    r"programme|recognise)\b",
    re.IGNORECASE,
)
LATIN_ABBREVIATIONS = re.compile(r"\b(?:e\.g\.|i\.e\.|etc\.)", re.IGNORECASE)
MARKDOWN_LINK = re.compile(r"\[([^\]]+)\]\([^\)]+\)")
INLINE_CODE = re.compile(r"`[^`]*`")
RAW_URL = re.compile(r"https?://\S+")
LIST_PREFIX = re.compile(r"^\s*(?:[-+*]|\d+[.)]|[A-Za-z][.)])\s+")
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")


@dataclass(frozen=True)
class Finding:
    severity: str
    rule: str
    path: str
    line: int
    message: str
    text: str


@dataclass(frozen=True)
class Block:
    text: str
    line: int
    mode: str
    is_list_item: bool = False


def clean_inline(text: str) -> str:
    """Remove machine-facing Markdown fragments but preserve link labels."""

    text = MARKDOWN_LINK.sub(r"\1", text)
    text = INLINE_CODE.sub(" CODE ", text)
    text = RAW_URL.sub(" URL ", text)
    text = re.sub(r"!\[([^\]]*)\]", r"\1", text)
    text = re.sub(r"[*_~]", "", text)
    return text


def first_word(text: str) -> str:
    match = re.search(r"[A-Za-z]+", clean_inline(text))
    return match.group(0).lower() if match else ""


def infer_mode(text: str, section_mode: str, requested_mode: str) -> str:
    if requested_mode != "auto":
        return requested_mode
    if section_mode == "procedural" or first_word(text) in IMPERATIVE_VERBS:
        return "procedural"
    return "descriptive"


def iter_blocks(text: str, requested_mode: str) -> Iterator[Block]:
    lines = text.splitlines()
    in_fence = False
    fence_marker = ""
    in_frontmatter = bool(lines and lines[0].strip() == "---")
    section_mode = "descriptive"
    paragraph: list[str] = []
    paragraph_line = 1

    def flush() -> Iterator[Block]:
        nonlocal paragraph
        if paragraph:
            joined = " ".join(part.strip() for part in paragraph)
            yield Block(
                joined,
                paragraph_line,
                infer_mode(joined, section_mode, requested_mode),
            )
            paragraph = []

    for number, raw in enumerate(lines, 1):
        stripped = raw.strip()
        if in_frontmatter:
            if number > 1 and stripped == "---":
                in_frontmatter = False
            continue
        fence_match = FENCE.match(raw)
        if fence_match:
            marker = fence_match.group(1)[0]
            if not in_fence:
                yield from flush()
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
            continue
        if in_fence:
            continue
        heading_match = HEADING.match(raw)
        if heading_match:
            yield from flush()
            section_mode = (
                "procedural"
                if PROCEDURAL_HEADINGS.search(heading_match.group(2))
                else "descriptive"
            )
            continue
        if not stripped:
            yield from flush()
            continue
        if (
            raw.startswith(("    ", "\t"))
            or stripped.startswith(("|", ">", "<!--"))
            or re.match(r"^\[[^\]]+\]:\s+", stripped)
            or re.match(r"^[-:| ]{3,}$", stripped)
        ):
            yield from flush()
            continue
        list_match = LIST_PREFIX.match(raw)
        if list_match:
            yield from flush()
            item = raw[list_match.end():].strip()
            if item:
                yield Block(
                    item,
                    number,
                    infer_mode(item, section_mode, requested_mode),
                    True,
                )
            continue
        if not paragraph:
            paragraph_line = number
        paragraph.append(raw)
    yield from flush()


def protect_sentence_periods(text: str) -> str:
    text = re.sub(r"\b([A-Za-z])\.([A-Za-z])\.", r"\1§\2§", text)
    text = re.sub(r"(?<=\d)\.(?=\d)", "§", text)
    text = re.sub(r"\b(?:Mr|Mrs|Ms|Dr|No|Fig|Eq)\.", lambda m: m.group(0)[:-1] + "§", text)
    return text


def split_sentences(text: str) -> list[str]:
    protected = protect_sentence_periods(clean_inline(text))
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", protected)
    return [part.replace("§", ".").strip() for part in parts if part.strip()]


def ste_word_count(sentence: str) -> int:
    text = clean_inline(sentence)
    text = re.sub(r"\([^()]*\)", " PAREN ", text)
    text = re.sub(r'“[^”]*”|"[^"]*"', " QUOTED ", text)
    text = re.sub(
        r"\b\d+(?:\.\d+)?\s*(?:%|°[CF]?|A|cm|ft|g|h|Hz|in|kg|km|kPa|L|lb|m|"
        r"mA|mg|min|mm|Nm|ohm|psi|s|V|W)\b",
        " MEASURE ",
        text,
        flags=re.IGNORECASE,
    )
    words = re.findall(r"\b[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*\b", text)
    return len(words)


def sentence_excerpt(sentence: str, limit: int = 140) -> str:
    collapsed = " ".join(sentence.split())
    return collapsed if len(collapsed) <= limit else collapsed[: limit - 1] + "…"


def line_findings(path: str, line: int, text: str) -> Iterator[Finding]:
    cleaned = clean_inline(text)
    if ";" in cleaned:
        yield Finding("error", "STE-8.1", path, line, "Semicolons are not permitted.", sentence_excerpt(text))
    for match in CONTRACTIONS.finditer(cleaned):
        yield Finding(
            "error",
            "STE-4.2",
            path,
            line,
            f"Write the contraction '{match.group(0)}' in full.",
            sentence_excerpt(text),
        )
    for match in BRITISH_SPELLINGS.finditer(cleaned):
        yield Finding(
            "warning",
            "STE-1.14",
            path,
            line,
            f"Check '{match.group(0)}' against the controlling spelling directive.",
            sentence_excerpt(text),
        )
    if LATIN_ABBREVIATIONS.search(cleaned):
        yield Finding(
            "warning",
            "STE-GR-6",
            path,
            line,
            "Replace or review the Latin abbreviation.",
            sentence_excerpt(text),
        )


def block_findings(path: str, block: Block) -> Iterator[Finding]:
    sentences = split_sentences(block.text)
    limit = 20 if block.mode == "procedural" else 25
    for sentence in sentences:
        count = ste_word_count(sentence)
        if count > limit:
            yield Finding(
                "error",
                "STE-5.1" if block.mode == "procedural" else "STE-6.3",
                path,
                block.line,
                f"{block.mode.title()} sentence has {count} words; maximum is {limit}.",
                sentence_excerpt(sentence),
            )
        if PASSIVE_VOICE.search(sentence):
            yield Finding(
                "warning",
                "STE-3.6",
                path,
                block.line,
                "Review likely passive voice; it is permitted only in a limited descriptive case.",
                sentence_excerpt(sentence),
            )
        if block.mode == "procedural":
            command_pattern = r"\b(?:and|then)\s+(?:" + "|".join(sorted(IMPERATIVE_VERBS)) + r")\b"
            if re.search(command_pattern, sentence, re.IGNORECASE):
                yield Finding(
                    "warning",
                    "STE-5.2",
                    path,
                    block.line,
                    "Review possible multiple instructions; keep them together only if they occur at the same time.",
                    sentence_excerpt(sentence),
                )
    if block.mode == "descriptive" and not block.is_list_item and len(sentences) > 6:
        yield Finding(
            "error",
            "STE-6.6",
            path,
            block.line,
            f"Paragraph has {len(sentences)} sentences; maximum is 6.",
            sentence_excerpt(block.text),
        )
    upper = block.text.upper()
    if upper.startswith("NOTE:") and first_word(block.text[5:]) in IMPERATIVE_VERBS:
        yield Finding(
            "error",
            "STE-5.5",
            path,
            block.line,
            "A note must give information, not an instruction.",
            sentence_excerpt(block.text),
        )
    if upper.startswith(("WARNING:", "CAUTION:")) and not re.search(
        r"\b(?:cause|damage|death|injury|prevent|result|risk)\b", block.text, re.IGNORECASE
    ):
        yield Finding(
            "warning",
            "STE-7.3",
            path,
            block.line,
            "Check that the safety instruction states the risk or possible result.",
            sentence_excerpt(block.text),
        )


def check_text(path: str, text: str, mode: str) -> list[Finding]:
    findings: list[Finding] = []
    blocks = list(iter_blocks(text, mode))
    for block in blocks:
        findings.extend(line_findings(path, block.line, block.text))
        findings.extend(block_findings(path, block))
    return findings


def iter_paths(inputs: Sequence[str]) -> Iterator[Path]:
    seen: set[Path] = set()
    for raw in inputs:
        path = Path(raw)
        if path.is_file():
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                yield path
            continue
        if path.is_dir():
            for candidate in sorted(path.rglob("*")):
                if any(part in EXCLUDED_DIRECTORIES for part in candidate.parts):
                    continue
                if candidate.is_file() and candidate.suffix.lower() in TEXT_EXTENSIONS:
                    resolved = candidate.resolve()
                    if resolved not in seen:
                        seen.add(resolved)
                        yield candidate
            continue
        raise FileNotFoundError(raw)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check documentation for detectable ASD-STE100 Issue 9 violations."
    )
    parser.add_argument("paths", nargs="+", help="Documentation files or directories")
    parser.add_argument(
        "--mode",
        choices=("auto", "descriptive", "procedural"),
        default="auto",
        help="Text type; auto uses headings and imperative-list heuristics",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Return a non-zero status when heuristic warnings remain",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    all_findings: list[Finding] = []
    checked = 0
    try:
        for path in iter_paths(args.paths):
            text = path.read_text(encoding="utf-8")
            all_findings.extend(check_text(str(path), text, args.mode))
            checked += 1
    except (FileNotFoundError, OSError, UnicodeError) as exc:
        print(f"check_ste.py: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps({"checked": checked, "findings": [asdict(item) for item in all_findings]}, indent=2))
    else:
        for item in all_findings:
            print(
                f"{item.path}:{item.line}: {item.severity.upper()} {item.rule}: "
                f"{item.message} [{item.text}]"
            )
        errors = sum(item.severity == "error" for item in all_findings)
        warnings = sum(item.severity == "warning" for item in all_findings)
        print(f"Checked {checked} file(s): {errors} error(s), {warnings} warning(s).")

    has_error = any(item.severity == "error" for item in all_findings)
    has_warning = any(item.severity == "warning" for item in all_findings)
    return 1 if has_error or (args.fail_on_warning and has_warning) else 0


if __name__ == "__main__":
    raise SystemExit(main())
