import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const inputPath = "C:/Users/PC/Downloads/Structuration des données_Chapitre PAAR-net_Renseigné.xlsx";
const input = await FileBlob.load(inputPath);
const workbook = await SpreadsheetFile.importXlsx(input);

const overview = await workbook.inspect({
  kind: "workbook,sheet,table",
  maxChars: 10000,
  tableMaxRows: 12,
  tableMaxCols: 24,
  tableMaxCellChars: 140,
});
console.log(overview.ndjson);

const sheet = workbook.worksheets.getItem("Fiches-actions");
const region = await workbook.inspect({
  kind: "region",
  sheetId: "Fiches-actions",
  range: "A1:Z80",
  maxChars: 30000,
  tableMaxRows: 80,
  tableMaxCols: 26,
  tableMaxCellChars: 160,
});
console.log(region.ndjson);

const style = await workbook.inspect({
  kind: "computedStyle",
  sheetId: "Fiches-actions",
  range: "A1:Z12",
  maxChars: 12000,
});
console.log(style.ndjson);
