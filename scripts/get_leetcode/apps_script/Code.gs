const SHEET_NAME_PATTERN = /^leetcode_[a-z0-9]+(?:-[a-z0-9]+)*$/;
const SHEET_HEADERS = ["title", "link", "tag", "is_uploaded"];


function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("LeetCode CSV")
    .addItem("Download pending CSV", "showPendingCsvDialog")
    .addToUi();
}


function showPendingCsvDialog() {
  try {
    const exportData = getPendingExport_();
    if (exportData.rows.length === 0) {
      SpreadsheetApp.getUi().alert(
        "No pending rows",
        "The active worksheet has no rows with a blank is_uploaded value.",
        SpreadsheetApp.getUi().ButtonSet.OK
      );
      return;
    }

    const template = HtmlService.createTemplateFromFile("ExportDialog");
    template.exportDataJson = safeJsonForHtml_(exportData);
    const dialog = template.evaluate().setWidth(480).setHeight(300);
    SpreadsheetApp.getUi().showModalDialog(dialog, "Download pending CSV");
  } catch (error) {
    SpreadsheetApp.getUi().alert(
      "Cannot prepare CSV",
      error.message,
      SpreadsheetApp.getUi().ButtonSet.OK
    );
  }
}


function getPendingExport_() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const sheetName = sheet.getName();

  if (!SHEET_NAME_PATTERN.test(sheetName)) {
    throw new Error(
      "Select a staging worksheet named leetcode_<category> before exporting."
    );
  }

  const values = sheet.getDataRange().getDisplayValues();
  if (values.length === 0) {
    throw new Error("The active worksheet is empty.");
  }

  const headers = values[0].slice(0, SHEET_HEADERS.length);
  if (headers.join("|") !== SHEET_HEADERS.join("|")) {
    throw new Error(
      "The worksheet headers must be: " + SHEET_HEADERS.join(", ")
    );
  }

  const rows = [];
  const rowReferences = [];

  for (let index = 1; index < values.length; index += 1) {
    const row = values[index];
    const title = (row[0] || "").trim();
    const link = (row[1] || "").trim();
    const tag = (row[2] || "").trim();
    const isUploaded = (row[3] || "").trim();

    if (isUploaded === "" && link !== "") {
      rows.push([title, link, tag]);
      rowReferences.push({ rowNumber: index + 1, link: link });
    }
  }

  const category = sheetName.substring("leetcode_".length);
  const date = Utilities.formatDate(
    new Date(),
    Session.getScriptTimeZone(),
    "yyyy-MM-dd"
  );

  return {
    filename: `leetcode-${category}-pending-${date}.csv`,
    sheetName: sheetName,
    rows: rows,
    rowReferences: rowReferences,
  };
}


function markRowsUploaded(sheetName, rowReferences) {
  if (!SHEET_NAME_PATTERN.test(sheetName)) {
    throw new Error("Invalid staging worksheet name.");
  }
  if (!Array.isArray(rowReferences) || rowReferences.length === 0) {
    throw new Error("No exported rows were supplied for confirmation.");
  }

  const lock = LockService.getDocumentLock();
  lock.waitLock(30000);

  try {
    const sheet = SpreadsheetApp.getActive().getSheetByName(sheetName);
    if (!sheet) {
      throw new Error(`Worksheet not found: ${sheetName}`);
    }

    rowReferences.forEach((reference) => {
      const rowNumber = reference.rowNumber;
      if (!Number.isInteger(rowNumber) || rowNumber < 2) {
        throw new Error("The export contained an invalid worksheet row number.");
      }

      const currentLink = String(sheet.getRange(rowNumber, 2).getDisplayValue()).trim();
      if (currentLink !== reference.link) {
        throw new Error(
          `Row ${rowNumber} changed after the CSV was prepared. No statuses were changed.`
        );
      }
    });

    let updatedCount = 0;
    rowReferences.forEach((reference) => {
      const rowNumber = reference.rowNumber;
      const statusCell = sheet.getRange(rowNumber, 4);
      if (String(statusCell.getDisplayValue()).trim() === "") {
        statusCell.setValue(1);
        updatedCount += 1;
      }
    });

    SpreadsheetApp.flush();
    return updatedCount;
  } finally {
    lock.releaseLock();
  }
}


function safeJsonForHtml_(value) {
  return JSON.stringify(value)
    .replace(/&/g, "\\u0026")
    .replace(/</g, "\\u003c")
    .replace(/>/g, "\\u003e")
    .replace(/\u2028/g, "\\u2028")
    .replace(/\u2029/g, "\\u2029");
}
