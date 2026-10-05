import json
from unittest.mock import patch, MagicMock
import pytest
from bot.vision import parse_receipt_gemini, TransactionDetails

def test_transaction_details_schema():
    details = TransactionDetails(
        is_payment_receipt=True,
        amount=1450.75,
        currency="INR",
        payee="Zomato",
        source_app="PhonePe",
        upi_ref_id="429182910291",
        date="05-Oct-2026",
        time="01:15 PM",
        category="Food",
        notes="Lunch order",
        debited_account="HDFC **1234"
    )
    assert details.is_payment_receipt is True
    assert details.amount == 1450.75
    assert details.payee == "Zomato"
    assert details.category == "Food"

def test_parse_receipt_gemini_mocked():
    mock_payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps({
                                "is_payment_receipt": True,
                                "amount": 250.0,
                                "currency": "INR",
                                "payee": "Starbucks Coffee",
                                "source_app": "GPay",
                                "upi_ref_id": "123456789012",
                                "date": "05-Oct-2026",
                                "time": "11:00 AM",
                                "category": "Food",
                                "notes": "Morning coffee",
                                "debited_account": "SBI **5544"
                            })
                        }
                    ]
                }
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(mock_payload).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = parse_receipt_gemini(
            image_bytes=b"fake_image_bytes",
            api_key="test_key",
            user_caption="coffee"
        )
        assert res.is_payment_receipt is True
        assert res.amount == 250.0
        assert res.payee == "Starbucks Coffee"
        assert res.category == "Food"
        assert res.source_app == "GPay"

def test_parse_receipt_gemini_503_retry():
    import urllib.error
    import io

    mock_success = MagicMock()
    mock_success.read.return_value = json.dumps({
        "candidates": [{
            "content": {"parts": [{"text": json.dumps({"is_payment_receipt": True, "amount": 100.0})}]}
        }]
    }).encode("utf-8")
    mock_success.__enter__.return_value = mock_success

    # First call raises 503, second call succeeds
    error_fp = io.BytesIO(b'{"error": "high demand"}')
    err_503 = urllib.error.HTTPError("http://test", 503, "Service Unavailable", {}, error_fp)

    with patch("urllib.request.urlopen", side_effect=[err_503, mock_success]), patch("time.sleep") as mock_sleep:
        res = parse_receipt_gemini(
            image_bytes=b"fake_image",
            api_key="test_key",
            base_delay=0.1
        )
        assert res.is_payment_receipt is True
        assert res.amount == 100.0
        mock_sleep.assert_called_once()
