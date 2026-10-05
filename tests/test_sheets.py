from unittest.mock import MagicMock, patch
import pytest
from bot.sheets import SheetsManager, SHEET_COLUMNS
from bot.vision import TransactionDetails

def test_sheets_manager_headers_and_append():
    mock_ws = MagicMock()
    mock_ws.row_values.return_value = []
    mock_ws.col_values.return_value = ["Timestamp", "2026-10-05 11:00:00"]

    mock_spreadsheet = MagicMock()
    mock_spreadsheet.worksheet.return_value = mock_ws

    mock_client = MagicMock()
    mock_client.open_by_key.return_value = mock_spreadsheet

    sm = SheetsManager(
        credentials_dict={"type": "service_account"},
        spreadsheet_id="test_sheet_id",
        sheet_name="Transactions"
    )
    sm._client = mock_client

    # Test worksheet retrieval and header setup
    ws = sm.get_worksheet()
    mock_ws.append_row.assert_any_call(SHEET_COLUMNS)

    # Test appending a transaction
    details = TransactionDetails(
        is_payment_receipt=True,
        amount=999.0,
        payee="Decathlon Sports",
        source_app="PhonePe",
        upi_ref_id="429182910291",
        category="Sports",
        notes="Shoes"
    )

    row_idx = sm.append_transaction(details, telegram_msg_id=101)
    assert row_idx == 2  # col_values length returned 2

    # Test category update
    sm.update_category(row_index=2, new_category="Sports")
    mock_ws.update_cell.assert_called_with(2, 6, "Sports")
