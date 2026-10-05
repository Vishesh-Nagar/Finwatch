import datetime
from typing import Optional, Dict, Any, List
import gspread
from google.oauth2.service_account import Credentials
from bot.vision import TransactionDetails

SHEET_COLUMNS = [
    "Timestamp",
    "Date",
    "Time",
    "Amount",
    "Payee",
    "Category",
    "Payment App",
    "UPI Ref / UTR",
    "Debited Account",
    "Notes",
    "Telegram Msg ID"
]

CATEGORY_COL_INDEX = 6   # Column F (1-indexed)
NOTES_COL_INDEX = 10     # Column J (1-indexed)

class SheetsManager:
    def __init__(self, credentials_dict: Dict[str, Any], spreadsheet_id: str, sheet_name: str = "Transactions"):
        self.credentials_dict = credentials_dict
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        self._client: Optional[gspread.Client] = None
        self._worksheet: Optional[gspread.Worksheet] = None

    def _get_client(self) -> gspread.Client:
        if self._client is None:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = Credentials.from_service_account_info(self.credentials_dict, scopes=scopes)
            self._client = gspread.authorize(creds)
        return self._client

    def get_worksheet(self) -> gspread.Worksheet:
        if self._worksheet is None:
            client = self._get_client()
            spreadsheet = client.open_by_key(self.spreadsheet_id)
            try:
                self._worksheet = spreadsheet.worksheet(self.sheet_name)
            except gspread.WorksheetNotFound:
                self._worksheet = spreadsheet.add_worksheet(title=self.sheet_name, rows=1000, cols=15)
            self._ensure_headers(self._worksheet)
        return self._worksheet

    def _ensure_headers(self, worksheet: gspread.Worksheet) -> None:
        """Ensures headers exist and formats them."""
        first_row = worksheet.row_values(1)
        if not first_row:
            worksheet.append_row(SHEET_COLUMNS)
            worksheet.freeze(rows=1)
            # Apply bold formatting to header row
            worksheet.format("A1:K1", {"textFormat": {"bold": True}})

    def is_duplicate_ref(self, upi_ref_id: Optional[str]) -> bool:
        """Checks if a UPI Ref ID / UTR is already recorded in the sheet."""
        if not upi_ref_id or len(upi_ref_id.strip()) < 6:
            return False
        ws = self.get_worksheet()
        # UPI Ref is in Column H (col 8)
        col_values = ws.col_values(8)
        return upi_ref_id.strip() in [val.strip() for val in col_values]

    def append_transaction(self, details: TransactionDetails, telegram_msg_id: int) -> int:
        """
        Appends a new transaction row to the Google Sheet.
        Returns the 1-based index of the newly added row.
        """
        ws = self.get_worksheet()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_str = details.date or datetime.datetime.now().strftime("%d-%b-%Y")
        time_str = details.time or datetime.datetime.now().strftime("%I:%M %p")

        row = [
            now_str,
            date_str,
            time_str,
            details.amount if details.amount is not None else 0.0,
            details.payee or "Unknown Payee",
            details.category or "Other",
            details.source_app or "UPI",
            details.upi_ref_id or "",
            details.debited_account or "",
            details.notes or "",
            str(telegram_msg_id)
        ]

        ws.append_row(row, value_input_option="USER_ENTERED")
        # Return row count after append
        return len(ws.col_values(1))

    def update_category(self, row_index: int, new_category: str) -> None:
        """Updates the category cell (Column F) for a specific row."""
        ws = self.get_worksheet()
        ws.update_cell(row_index, CATEGORY_COL_INDEX, new_category)

    def update_notes(self, row_index: int, new_notes: str) -> None:
        """Updates or appends to the notes cell (Column J) for a specific row."""
        ws = self.get_worksheet()
        current_notes = ws.cell(row_index, NOTES_COL_INDEX).value or ""
        combined = f"{current_notes}; {new_notes}".strip("; ") if current_notes else new_notes
        ws.update_cell(row_index, NOTES_COL_INDEX, combined)
