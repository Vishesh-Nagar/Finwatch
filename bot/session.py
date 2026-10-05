import time
from typing import Dict, Any, Optional
from bot.vision import TransactionDetails

CATEGORY_KEYWORDS = {
    "Food": ["food", "lunch", "dinner", "breakfast", "snacks", "coffee", "tea", "cafe", "restaurant", "swiggy", "zomato", "eat", "burger", "pizza"],
    "Travel": ["travel", "cab", "uber", "ola", "auto", "rapido", "flight", "train", "metro", "bus", "fuel", "petrol", "diesel", "toll"],
    "Sports": ["sports", "gym", "badminton", "fitness", "decathlon", "turf", "cricket", "football", "swimming", "workout"],
    "Shopping": ["shopping", "clothes", "amazon", "flipkart", "shoes", "electronics", "mall", "myntra"],
    "Bills": ["bills", "bill", "electricity", "recharge", "wifi", "internet", "gas", "water", "rent", "maintenance", "bescom"],
    "Groceries": ["groceries", "grocery", "blinkit", "zepto", "instamart", "vegetables", "fruits", "supermarket", "milk"],
    "Entertainment": ["entertainment", "movie", "cinema", "bookmyshow", "games", "gaming", "concert", "show"],
    "Health": ["health", "medicine", "medical", "doctor", "pharmacy", "apollo", "hospital", "clinic", "lab"]
}

STANDARD_CATEGORIES = list(CATEGORY_KEYWORDS.keys()) + ["Other"]

class SessionManager:
    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self._sessions: Dict[int, Dict[str, Any]] = {}

    def set_active_transaction(
        self,
        user_id: int,
        row_index: int,
        bot_msg_id: int,
        details: TransactionDetails
    ) -> None:
        self._sessions[user_id] = {
            "row_index": row_index,
            "bot_msg_id": bot_msg_id,
            "details": details,
            "created_at": time.time()
        }

    def get_active_transaction(self, user_id: int) -> Optional[Dict[str, Any]]:
        session = self._sessions.get(user_id)
        if not session:
            return None
        
        # Check if session expired
        if time.time() - session["created_at"] > self.ttl_seconds:
            del self._sessions[user_id]
            return None
        
        return session

    def clear_active_transaction(self, user_id: int) -> None:
        if user_id in self._sessions:
            del self._sessions[user_id]

    @staticmethod
    def match_category(text: str) -> Optional[str]:
        """
        Attempts to match free text to a known standard category.
        Returns category string if matched, otherwise None.
        """
        text_lower = text.strip().lower()
        
        # Exact match with category name
        for cat in STANDARD_CATEGORIES:
            if text_lower == cat.lower():
                return cat
                
        # Keyword matching
        for cat, keywords in CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower.split() or text_lower == kw:
                    return cat

        return None
