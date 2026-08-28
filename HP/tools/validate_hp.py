from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
VALID_CATEGORIES = {"論文", "学会", "受賞", "その他"}
UNTRACKED_LINK_ROOTS = {"album", "oldsite"}
MANAGED_ROOT_HTML = {
    "index.html",
    "Member.html",
    "Album.html",
    "Publication.html",
    "Research.html",
    "Research_EN.html",
    "Contact.html",
    "Link.html",
}

VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}

OPTIONAL_CLOSE_TAGS = {
    "body",
    "colgroup",
    "dd",
    "dt",
    "head",
    "html",
    "li",
    "option",
    "p",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
}

SKIP_DIRS = {".git", ".github", "album", "oldsite"}


@dataclass
class Finding:
    path: Path
    message: str
    line: int | None = None

    def format(self) -> str:
        rel = self.path.relative_to(ROOT)
        if self.line is None:
            return f"{rel}: {self.message}"
        return f"{rel}:{self.line}: {self.message}"


class Validator:
    def __init__(self) -> None:
        self.findings: list[Finding] = []

    def error(self, path: Path, message: str, line: int | None = None) -> None:
        self.findings.append(Finding(path, message, line))


class StructureParser(HTMLParser):
    def __init__(self, path: Path, validator: Validator) -> None:
        super().__init__(convert_charrefs=True)
        self.path = path
        self.validator = validator
        self.stack: list[tuple[str, int]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in VOID_TAGS:
            return
        self.stack.append((tag, self.getpos()[0]))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        return

    def handle_endtag(self, tag: str) -> None:
        if tag in VOID_TAGS:
            return

        for index in range(len(self.stack) - 1, -1, -1):
            open_tag, _line = self.stack[index]
            if open_tag == tag:
                unclosed = self.stack[index + 1 :]
                for unclosed_tag, unclosed_line in unclosed:
                    if unclosed_tag not in OPTIONAL_CLOSE_TAGS:
                        self.validator.error(
                            self.path,
                            f"<{unclosed_tag}> が </{tag}> の前に閉じられていません",
                            unclosed_line,
                        )
                del self.stack[index:]
                return

        self.validator.error(self.path, f"対応する開始タグのない </{tag}> があります", self.getpos()[0])

    def close(self) -> None:
        super().close()
        for tag, line in self.stack:
            if tag not in OPTIONAL_CLOSE_TAGS:
                self.validator.error(self.path, f"<{tag}> が閉じられていません", line)


class NewsParser(HTMLParser):
    def __init__(self, path: Path, validator: Validator) -> None:
        super().__init__(convert_charrefs=True)
        self.path = path
        self.validator = validator
        self.current_tag: str | None = None
        self.current_attrs: dict[str, str] = {}
        self.current_line: int | None = None
        self.text_parts: list[str] = []
        self.categories: list[tuple[str, int | None]] = []
        self.times: list[tuple[str, str, int | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {name: value or "" for name, value in attrs}
        if tag == "time" or attrs_dict.get("class") == "category":
            self.current_tag = tag
            self.current_attrs = attrs_dict
            self.current_line = self.getpos()[0]
            self.text_parts = []

    def handle_data(self, data: str) -> None:
        if self.current_tag:
            self.text_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if not self.current_tag:
            return
        if tag != self.current_tag and not (self.current_attrs.get("class") == "category" and tag == "span"):
            return

        text = "".join(self.text_parts).strip()
        if self.current_tag == "time":
            self.times.append((self.current_attrs.get("datetime", ""), text, self.current_line))
        elif self.current_attrs.get("class") == "category":
            self.categories.append((text, self.current_line))

        self.current_tag = None
        self.current_attrs = {}
        self.current_line = None
        self.text_parts = []


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str, str, int]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {name: value or "" for name, value in attrs}
        for attr in ("href", "src", "data"):
            if attr in attrs_dict:
                self.links.append((tag, attr, attrs_dict[attr], self.getpos()[0]))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def html_files() -> Iterable[Path]:
    for name in sorted(MANAGED_ROOT_HTML):
        path = ROOT / name
        if path.exists():
            yield path


def check_structure(path: Path, validator: Validator) -> None:
    parser = StructureParser(path, validator)
    try:
        parser.feed(read_text(path))
        parser.close()
    except Exception as exc:
        validator.error(path, f"HTMLの解析に失敗しました: {exc}")


def latest_year_section(text: str) -> str:
    match = re.search(
        r'(<h2[^>]*id="\d{4}y"[^>]*>.*?</h2>\s*<ul\s+class="news-list"\s*>.*?</ul>)',
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    return match.group(1) if match else text


def check_news_rules(path: Path, validator: Validator, latest_year_only: bool = False) -> None:
    parser = NewsParser(path, validator)
    text = read_text(path)
    if latest_year_only:
        text = latest_year_section(text)
    parser.feed(text)
    parser.close()

    for datetime_value, visible_text, line in parser.times:
        if not re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}(?:-\d{1,2})?", datetime_value):
            validator.error(path, f'datetime="{datetime_value}" はゼロなし YYYY-M-D 形式にしてください', line)

        if not re.fullmatch(r"\d{4}\.\d{1,2}\.\d{1,2}(?:-\d{1,2})?(?:申込締切)?", visible_text):
            validator.error(path, f"表示日付「{visible_text}」は YYYY.M.D 形式にしてください", line)

    for category, line in parser.categories:
        if category not in VALID_CATEGORIES:
            validator.error(path, f"カテゴリ「{category}」は {', '.join(sorted(VALID_CATEGORIES))} のいずれかにしてください", line)


def count_index_news_items(text: str) -> int:
    match = re.search(r'<div\s+class="news-list"\s*>\s*<ul>(.*?)</ul>', text, flags=re.DOTALL | re.IGNORECASE)
    if not match:
        return 0
    return len(re.findall(r"<li\b", match.group(1), flags=re.IGNORECASE))


def check_index_news_count(validator: Validator) -> None:
    path = ROOT / "index.html"
    count = count_index_news_items(read_text(path))
    if count > 10:
        validator.error(path, f"トップページのニュースが {count} 件あります。10件以内にしてください")


def should_check_target(path: Path, target_value: str) -> bool:
    normalized = target_value.replace("\\", "/")
    normalized = normalized.removeprefix("./")
    first_part = normalized.split("/", 1)[0]
    if first_part in UNTRACKED_LINK_ROOTS:
        return False
    return True


def resolve_local_target(base: Path, value: str) -> Path | None:
    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc:
        return None
    if value.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None

    local_path = unquote(parsed.path)
    if not local_path:
        return None
    return (base.parent / local_path).resolve()


def check_local_links(path: Path, validator: Validator) -> None:
    parser = LinkParser()
    parser.feed(read_text(path))
    parser.close()

    root_resolved = ROOT.resolve()
    for _tag, attr, value, line in parser.links:
        if not should_check_target(path, value):
            continue

        target = resolve_local_target(path, value)
        if target is None:
            continue

        if target != root_resolved and root_resolved not in target.parents:
            validator.error(path, f"{attr} がHPフォルダ外を参照しています: {value}", line)
            continue

        if not target.exists():
            validator.error(path, f"{attr} の参照先が存在しません: {value}", line)


def check_album_folder_names(validator: Validator) -> None:
    album_dir = ROOT / "album"
    if not album_dir.exists():
        return

    for child in album_dir.iterdir():
        if child.is_dir() and not re.fullmatch(r"\d{12}", child.name):
            if child.name == "__pycache__":
                continue
            validator.error(child, "アルバムフォルダ名は YYYYMMDDhhmm の12桁にしてください")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    validator = Validator()

    for path in html_files():
        check_structure(path, validator)
        check_local_links(path, validator)

    news_path = ROOT / "News.html"
    if news_path.exists():
        check_news_rules(news_path, validator, latest_year_only=True)

    index_path = ROOT / "index.html"
    if index_path.exists():
        check_news_rules(index_path, validator)

    check_index_news_count(validator)

    if validator.findings:
        print("HP validation failed:")
        for finding in validator.findings:
            print(f"- {finding.format()}")
        return 1

    print("HP validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
