import argparse
import csv
import json
import os
import re
import gspread
from pathlib import Path

from dotenv import load_dotenv


CSV_COLUMNS = ("title", "link", "tag")
SHEET_COLUMNS = ("problem", "tag", "is_uploaded")
LEGACY_SHEET_COLUMNS = ("title", "link", "tag", "is_uploaded")
DATA_DIRECTORY = Path(__file__).resolve().parent / "data"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CATEGORY_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HYPERLINK_PATTERN = re.compile(r'^=HYPERLINK\("((?:""|[^"])*)"\s*,', re.IGNORECASE)
GOOGLE_SHEETS_SCOPES = ("https://www.googleapis.com/auth/spreadsheets",)


def category_slug(value: str) -> str:
    category = value.strip().lower()
    if not CATEGORY_PATTERN.fullmatch(category):
        raise argparse.ArgumentTypeError(
            "category must contain lowercase letters, numbers, or single hyphens"
        )
    return category


def read_category_csv(csv_path: Path) -> list[dict[str, str]]:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV does not exist: {csv_path}")

    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if tuple(reader.fieldnames or ()) != CSV_COLUMNS:
            raise ValueError(
                f"{csv_path} must have exactly these columns: {', '.join(CSV_COLUMNS)}"
            )
        return [{column: row[column] for column in CSV_COLUMNS} for row in reader]


def escape_formula_string(value: str) -> str:
    return value.replace('"', '""')


def problem_formula(title: str, link: str) -> str:
    return (
        f'=HYPERLINK("{escape_formula_string(link)}",'
        f'"{escape_formula_string(title)}")'
    )


def link_from_problem_formula(formula: str) -> str:
    match = HYPERLINK_PATTERN.match(formula.strip())
    return match.group(1).replace('""', '"') if match else ""


def get_or_create_worksheet(spreadsheet, worksheet_name: str, minimum_rows: int):
    try:
        return spreadsheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=worksheet_name,
            rows=max(minimum_rows, 100),
            cols=len(SHEET_COLUMNS),
        )
        worksheet.update(
            values=[list(SHEET_COLUMNS)],
            range_name="A1:C1",
            value_input_option="RAW",
        )
        return worksheet


def migrate_legacy_worksheet(worksheet, sheet_values: list[list[str]]):
    migrated_values = [list(SHEET_COLUMNS)]

    for row in sheet_values[1:]:
        title = row[0] if len(row) > 0 else ""
        link = row[1] if len(row) > 1 else ""
        tag = row[2] if len(row) > 2 else ""
        is_uploaded = row[3] if len(row) > 3 else ""
        if link:
            migrated_values.append(
                [problem_formula(title, link), tag, is_uploaded]
            )

    worksheet.update(
        values=migrated_values,
        range_name=f"A1:C{len(migrated_values)}",
        value_input_option="USER_ENTERED",
    )
    worksheet.batch_clear([f"D1:D{max(len(sheet_values), 1)}"])
    return migrated_values


def append_missing_rows(worksheet, csv_rows: list[dict[str, str]]) -> int:
    sheet_values = worksheet.get_all_values(
        value_render_option=gspread.utils.ValueRenderOption.formula
    )

    if not sheet_values:
        worksheet.update(
            values=[list(SHEET_COLUMNS)],
            range_name="A1:C1",
            value_input_option="RAW",
        )
        sheet_values = [list(SHEET_COLUMNS)]

    if tuple(sheet_values[0]) == LEGACY_SHEET_COLUMNS:
        sheet_values = migrate_legacy_worksheet(worksheet, sheet_values)

    if tuple(sheet_values[0]) != SHEET_COLUMNS:
        raise ValueError(
            f"Worksheet {worksheet.title!r} must have exactly these columns: "
            f"{', '.join(SHEET_COLUMNS)}"
        )

    existing_links = {
        link_from_problem_formula(row[0])
        for row in sheet_values[1:]
        if row and link_from_problem_formula(row[0])
    }
    rows_to_append = []

    for row in csv_rows:
        if row["link"] in existing_links:
            continue
        rows_to_append.append(
            [problem_formula(row["title"], row["link"]), row["tag"], ""]
        )
        existing_links.add(row["link"])

    if rows_to_append:
        worksheet.append_rows(rows_to_append, value_input_option="USER_ENTERED")

    return len(rows_to_append)


def sync_category(
    category: str,
    spreadsheet_id: str,
    service_account_json: str,
) -> tuple[str, int, int]:
    import gspread

    try:
        credentials = json.loads(service_account_json)
    except json.JSONDecodeError as error:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON") from error

    csv_path = DATA_DIRECTORY / f"{category}.csv"
    csv_rows = read_category_csv(csv_path)
    client = gspread.service_account_from_dict(
        credentials,
        scopes=GOOGLE_SHEETS_SCOPES,
    )
    spreadsheet = client.open_by_key(spreadsheet_id)
    worksheet_name = f"leetcode_{category}"
    worksheet = get_or_create_worksheet(
        spreadsheet, worksheet_name, len(csv_rows) + 1
    )
    appended_count = append_missing_rows(worksheet, csv_rows)
    return worksheet_name, appended_count, len(csv_rows)


def required_environment_variable(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Required environment variable is missing: {name}")
    return value


def service_account_json_from_environment() -> str:
    inline_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if inline_json:
        return inline_json

    key_file = required_environment_variable("GOOGLE_SERVICE_ACCOUNT_FILE")
    key_path = Path(key_file).expanduser()
    if not key_path.is_absolute():
        key_path = REPOSITORY_ROOT / key_path

    try:
        return key_path.read_text(encoding="utf-8")
    except OSError as error:
        raise RuntimeError(
            f"Could not read GOOGLE_SERVICE_ACCOUNT_FILE: {key_path}"
        ) from error


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Append missing LeetCode CSV rows to a Google Sheets staging tab."
    )
    parser.add_argument(
        "--category",
        required=True,
        type=category_slug,
        help="LeetCode category slug matching a CSV in the data directory.",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv(REPOSITORY_ROOT / ".env")
    args = parse_args()
    worksheet_name, appended_count, total_count = sync_category(
        category=args.category,
        spreadsheet_id=required_environment_variable("GOOGLE_SPREADSHEET_ID"),
        service_account_json=service_account_json_from_environment(),
    )
    print(
        f"Synchronized {total_count} {args.category} problems with "
        f"{worksheet_name} ({appended_count} appended)."
    )


if __name__ == "__main__":
    main()
