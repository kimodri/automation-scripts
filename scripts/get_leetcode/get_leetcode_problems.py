import argparse
import csv
import json
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql/"
LEETCODE_PROBLEM_URL = "https://leetcode.com/problems/{title_slug}/"
PAGE_SIZE = 100
CSV_COLUMNS = ("title", "link", "tag")
DATA_DIRECTORY = Path(__file__).resolve().parent / "data"
CATEGORY_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def category_slug(value: str) -> str:
    category = value.strip().lower()
    if not CATEGORY_PATTERN.fullmatch(category):
        raise argparse.ArgumentTypeError(
            "category must contain lowercase letters, numbers, or single hyphens"
        )
    return category


def build_graphql_query(category: str) -> str:
    return f"""
query problemsetQuestionList($limit: Int, $skip: Int) {{
  problemsetQuestionList: questionList(
    categorySlug: "{category}"
    limit: $limit
    skip: $skip
    filters: {{}}
  ) {{
    totalNum
    problems: data {{
      title
      titleSlug
      isPaidOnly
    }}
  }}
}}
"""


def request_problem_page(category: str, skip: int) -> dict:
    payload = json.dumps(
        {
            "query": build_graphql_query(category),
            "variables": {"limit": PAGE_SIZE, "skip": skip},
        }
    ).encode("utf-8")
    request = Request(
        LEETCODE_GRAPHQL_URL,
        data=payload,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Referer": "https://leetcode.com/problemset/",
            "User-Agent": "Mozilla/5.0",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            result = json.load(response)
    except HTTPError as error:
        raise RuntimeError(
            f"LeetCode returned HTTP {error.code}: {error.reason}"
        ) from error
    except URLError as error:
        raise RuntimeError(f"Could not connect to LeetCode: {error.reason}") from error

    if errors := result.get("errors"):
        messages = "; ".join(error.get("message", str(error)) for error in errors)
        raise RuntimeError(f"LeetCode GraphQL error: {messages}")

    problem_list = result.get("data", {}).get("problemsetQuestionList")
    if problem_list is None:
        raise RuntimeError("LeetCode returned an unexpected response structure")

    return problem_list


def get_free_leetcode_problems(category: str) -> list[dict[str, str]]:
    fetched_problems = []
    skip = 0
    total_num = None

    while total_num is None or len(fetched_problems) < total_num:
        problem_page = request_problem_page(category, skip)
        total_num = problem_page["totalNum"]
        page = problem_page["problems"]

        if not page:
            break

        fetched_problems.extend(page)
        skip += len(page)

    if total_num is None or len(fetched_problems) < total_num:
        raise RuntimeError(
            f"LeetCode reported {total_num or 0} problems but returned "
            f"only {len(fetched_problems)}"
        )

    tag = f"leetcode::{category}"
    problems = []
    seen_links = set()

    for problem in fetched_problems:
        if problem["isPaidOnly"]:
            continue

        link = LEETCODE_PROBLEM_URL.format(title_slug=problem["titleSlug"])
        if link in seen_links:
            continue

        seen_links.add(link)
        problems.append({"title": problem["title"], "link": link, "tag": tag})

    return problems


def read_existing_csv(csv_path: Path) -> list[dict[str, str]]:
    if not csv_path.exists():
        return []

    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if tuple(reader.fieldnames or ()) != CSV_COLUMNS:
            raise ValueError(
                f"{csv_path} must have exactly these columns: {', '.join(CSV_COLUMNS)}"
            )
        return [{column: row[column] for column in CSV_COLUMNS} for row in reader]


def merge_new_problems(
    existing_problems: list[dict[str, str]],
    fetched_problems: list[dict[str, str]],
) -> tuple[list[dict[str, str]], int]:
    merged = list(existing_problems)
    seen_links = {problem["link"] for problem in existing_problems}

    for problem in fetched_problems:
        if problem["link"] in seen_links:
            continue
        merged.append(problem)
        seen_links.add(problem["link"])

    return merged, len(merged) - len(existing_problems)


def write_csv(csv_path: Path, problems: list[dict[str, str]]) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = csv_path.with_suffix(f"{csv_path.suffix}.tmp")

    with temporary_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(problems)

    temporary_path.replace(csv_path)


def update_category_csv(category: str) -> tuple[Path, int, int]:
    csv_path = DATA_DIRECTORY / f"{category}.csv"
    existing_problems = read_existing_csv(csv_path)
    fetched_problems = get_free_leetcode_problems(category)
    merged_problems, added_count = merge_new_problems(
        existing_problems, fetched_problems
    )

    if added_count or not csv_path.exists():
        write_csv(csv_path, merged_problems)

    return csv_path, added_count, len(merged_problems)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Incrementally save free LeetCode problems to a category CSV."
    )
    parser.add_argument(
        "--category",
        required=True,
        type=category_slug,
        help="LeetCode category slug, such as database or algorithms.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    csv_path, added_count, total_count = update_category_csv(args.category)
    print(
        f"Saved {total_count} free {args.category} problems to {csv_path} "
        f"({added_count} new)."
    )


if __name__ == "__main__":
    main()
