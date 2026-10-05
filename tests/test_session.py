import time
import pytest
from bot.session import SessionManager
from bot.vision import TransactionDetails

def test_session_lifecycle():
    sm = SessionManager(ttl_seconds=1)
    details = TransactionDetails(
        is_payment_receipt=True,
        amount=500.0,
        payee="Decathlon",
        source_app="GPay"
    )

    sm.set_active_transaction(user_id=123, row_index=2, bot_msg_id=456, details=details)
    active = sm.get_active_transaction(123)
    assert active is not None
    assert active["row_index"] == 2
    assert active["details"].amount == 500.0

    # Wait for TTL to expire
    time.sleep(1.2)
    assert sm.get_active_transaction(123) is None

def test_match_category():
    assert SessionManager.match_category("food") == "Food"
    assert SessionManager.match_category("lunch") == "Food"
    assert SessionManager.match_category("cab to office") == "Travel"
    assert SessionManager.match_category("uber") == "Travel"
    assert SessionManager.match_category("badminton court") == "Sports"
    assert SessionManager.match_category("gym") == "Sports"
    assert SessionManager.match_category("blinkit order") == "Groceries"
    assert SessionManager.match_category("electricity bill") == "Bills"
    assert SessionManager.match_category("random phrase without keyword") is None
