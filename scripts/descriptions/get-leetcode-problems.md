# Incremental LeetCode Problem Export

This automation collects all free LeetCode problems in a selected category, stores newly discovered problems in a repository CSV, and stages missing rows in Google Sheets. A bound Apps Script downloads only pending rows as a separate CSV and marks them as downloaded after confirmation.

The repository owns the problem catalog. Google Sheets alone owns the download state.

## Data Flow

1. The extractor retrieves every page for a LeetCode category and removes Premium problems.
2. It compares problem links with the existing category CSV and appends only unseen links.
3. The Sheets synchronizer appends repository links missing from the category's staging worksheet.
4. New worksheet rows receive a blank `is_uploaded` value.
5. The Apps Script downloads only blank-status rows and changes the confirmed batch to `1`.

## Requirements

- Python 3.10 or later
- Dependencies from `requirements.txt`
- A Google Cloud service account for automated Google Sheets access
- A Google spreadsheet shared with the service account

Install the Python dependencies from the repository root:

```text
python -m pip install -r requirements.txt
```

## Collect Problems Locally

Run the extractor from the repository root and provide a LeetCode category slug:

```text
python scripts/get_leetcode/get_leetcode_problems.py --category database
```

The command creates or updates:

```text
scripts/get_leetcode/data/database.csv
```

Each repository CSV contains exactly three columns:

```text
title,link,tag
```

The tag uses the selected category, such as `leetcode::database`. Repeating the command preserves existing rows and appends only links that are not already present.

## Configure Google Sheets Access

1. Create or select a Google Cloud project.
2. Enable the Google Sheets API.
3. Create a service account and download its JSON key.
4. Create the destination Google spreadsheet.
5. Share the spreadsheet with the JSON key's `client_email` as an editor.
6. Copy the spreadsheet ID from its URL. It is the value between `/d/` and `/edit`.

The workflow expects two GitHub Actions repository secrets:

| Secret | Value |
|---|---|
| `GOOGLE_SERVICE_ACCOUNT_JSON` | The complete contents of the service-account JSON key. |
| `GOOGLE_SPREADSHEET_ID` | The destination spreadsheet ID. |

Service accounts cannot access a private spreadsheet until it is explicitly shared with their email address. See the [gspread authentication guide](https://docs.gspread.org/en/master/oauth2.html) for the official setup process.

## Synchronize a Category Manually

Copy the environment template from the repository root:

```text
Copy-Item .env.example .env
```

Edit `.env` and provide the path to the downloaded service-account key and the spreadsheet ID:

```text
GOOGLE_SERVICE_ACCOUNT_FILE=C:/secure/your-service-account-key.json
GOOGLE_SPREADSHEET_ID=your-spreadsheet-id
```

Keep the JSON key outside the repository. The `.env` file is ignored by Git and is loaded automatically for local runs. Then run:

```text
python scripts/get_leetcode/sync_google_sheet.py --category database
```

The synchronizer creates a worksheet named `leetcode_database` when needed. Staging worksheets contain:

```text
title,link,tag,is_uploaded
```

Existing worksheet links are left unchanged. Missing links are appended with a blank `is_uploaded` cell.

## Install the Apps Script

1. Open the destination spreadsheet and select **Extensions > Apps Script**.
2. Replace the contents of `Code.gs` with `scripts/get_leetcode/apps_script/Code.gs`.
3. Add an HTML file named `ExportDialog` and copy in `scripts/get_leetcode/apps_script/ExportDialog.html`.
4. Save the project and reload the spreadsheet.
5. Approve the requested spreadsheet permissions the first time the script runs.
6. Open a worksheet named `leetcode_<category>` and select **LeetCode CSV > Download pending CSV**.

You can also assign the function `showPendingCsvDialog` to a drawing or image used as a sheet button.

The dialog downloads a UTF-8 CSV with these columns:

```text
title,link,tag
```

After locating the downloaded file, select **Mark batch as downloaded**. Only the rows included in that dialog are changed from blank to `1`. Closing the dialog without confirmation leaves their statuses blank.

## GitHub Actions

The `Update LeetCode problems` workflow runs every Monday at approximately 2:00 AM Asia/Manila time. Its scheduled run updates the `database` category. The workflow can also be started manually with another category slug.

Each run:

1. Runs the automated tests.
2. Updates the selected repository CSV.
3. Appends missing rows to the corresponding Google Sheets staging worksheet.
4. Commits the CSV only when new problems were discovered.

The workflow requires `contents: write` permission so its bot account can commit changed CSV data.

## Failure Behavior

- Invalid category slugs are rejected before a path or request is created.
- Incomplete LeetCode pagination stops the run instead of saving partial results.
- Unexpected CSV or worksheet headers stop synchronization.
- Google Sheets synchronization never resets existing status values.
- A failed or cancelled Apps Script export does not mark rows as downloaded.

[Back to the script list](../../README.md)
