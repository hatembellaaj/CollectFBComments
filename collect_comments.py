"""Command-line helper to collect Facebook post comments.

Provide a post URL and a Graph API access token to export comments to CSV
and print the first ten comments in a readable format.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from typing import IO, Iterable, List, Optional, Union
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen


POST_ID_PATTERN = re.compile(r"(?P<page>\d+)_+(?P<post>\d+)")


@dataclass
class Comment:
    """Represents a single Facebook comment."""

    comment_id: str
    created_time: str
    author_id: Optional[str]
    author_name: Optional[str]
    message: str
    parent_id: Optional[str]
    like_count: Optional[int]


class CommentCollector:
    """Collects comments for a Facebook post via the Graph API."""

    def __init__(self, access_token: str, api_version: str = "v19.0") -> None:
        self.access_token = access_token
        self.api_version = api_version

    def _fetch_page(self, url: str, params: Optional[dict] = None) -> dict:
        if params:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}{urlencode(params)}"

        request = Request(url)
        try:
            with urlopen(request, timeout=10) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                payload = response.read().decode(charset)
        except HTTPError as exc:
            # Match the requests.HTTPError API used in the CLI for simplicity
            raise

        return json.loads(payload)

    def _comment_from_json(self, raw: dict) -> Comment:
        return Comment(
            comment_id=raw.get("id", ""),
            created_time=raw.get("created_time", ""),
            author_id=(raw.get("from") or {}).get("id"),
            author_name=(raw.get("from") or {}).get("name"),
            message=raw.get("message", ""),
            parent_id=raw.get("parent", {}).get("id"),
            like_count=raw.get("like_count"),
        )

    def collect(self, post_id: str) -> List[Comment]:
        """Retrieve all comments for a post.

        Pagination is handled transparently. The filter is set to "stream" so
        we get threaded comments in chronological order.
        """

        comments: List[Comment] = []
        base_url = f"https://graph.facebook.com/{self.api_version}/{post_id}/comments"
        params = {
            "access_token": self.access_token,
            "summary": "true",
            "filter": "stream",
            "limit": 100,
        }

        url: Optional[str] = base_url
        while url:
            payload = self._fetch_page(url, params=params)
            params = None  # only include params on first request when a paging URL is not yet set

            for item in payload.get("data", []):
                comments.append(self._comment_from_json(item))

            paging = payload.get("paging", {})
            url = paging.get("next")

        return comments


def extract_post_id(post_url: str) -> str:
    """Attempt to derive a Graph API post id from a URL."""

    parsed = urlparse(post_url)

    # URLs such as https://www.facebook.com/story.php?story_fbid=<post>&id=<page>
    query = parse_qs(parsed.query)
    if "story_fbid" in query and "id" in query:
        return f"{query['id'][0]}_{query['story_fbid'][0]}"

    # Look for explicit page_post pattern anywhere in the URL
    match = POST_ID_PATTERN.search(post_url)
    if match:
        return match.group(0)

    # Common pattern: /<page>/posts/<post>
    parts = [segment for segment in parsed.path.split("/") if segment]
    if "posts" in parts:
        idx = parts.index("posts")
        if idx + 1 < len(parts):
            page_identifier = parts[0]
            post_identifier = parts[idx + 1]
            return f"{page_identifier}_{post_identifier}"

    if parts:
        # If we only have a single numeric component assume it's the post id itself
        if len(parts) == 1 and parts[0].isdigit():
            return parts[0]

    raise ValueError(
        "Unable to derive post id from URL. Provide a post id explicitly with --post-id."
    )


def save_comments_to_csv(
    comments: Iterable[Comment], output: Union[str, IO[str]]
) -> None:
    fieldnames = [
        "comment_id",
        "created_time",
        "author_id",
        "author_name",
        "message",
        "parent_id",
        "like_count",
    ]

    handle: Optional[IO[str]] = None
    close_handle = False

    if hasattr(output, "write"):
        handle = output  # type: ignore[assignment]
    else:
        handle = open(output, "w", newline="", encoding="utf-8")
        close_handle = True

    try:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for comment in comments:
            writer.writerow(
                {
                    "comment_id": comment.comment_id,
                    "created_time": comment.created_time,
                    "author_id": comment.author_id,
                    "author_name": comment.author_name,
                    "message": comment.message,
                    "parent_id": comment.parent_id,
                    "like_count": comment.like_count,
                }
            )
    finally:
        if close_handle and handle is not None:
            handle.close()


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Collect Facebook post comments using the Graph API and export them to a CSV file."
        )
    )
    parser.add_argument("post_url", help="URL of the Facebook post")
    parser.add_argument("access_token", help="Graph API access token")
    parser.add_argument(
        "--post-id",
        help="Graph API post id (skips URL parsing).",
    )
    parser.add_argument(
        "--csv",
        default="comments.csv",
        help="Destination CSV filename (default: comments.csv)",
    )
    parser.add_argument(
        "--api-version",
        default="v19.0",
        help="Graph API version prefix (default: v19.0)",
    )
    return parser.parse_args(argv)


def print_sample(comments: List[Comment], sample_size: int = 10) -> None:
    for comment in comments[:sample_size]:
        author = comment.author_name or "Unknown author"
        print(f"- {author}: {comment.message}")


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    try:
        post_id = args.post_id or extract_post_id(args.post_url)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    collector = CommentCollector(access_token=args.access_token, api_version=args.api_version)

    try:
        comments = collector.collect(post_id)
    except HTTPError as exc:
        print(f"Failed to fetch comments: {exc}", file=sys.stderr)
        return 1

    save_comments_to_csv(comments, args.csv)
    print(f"Fetched {len(comments)} comments. Saved to {args.csv}.")
    print("First 10 comments:")
    print_sample(comments)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
