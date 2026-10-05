import json
import base64
import urllib.request
import urllib.error
from typing import Optional
from pydantic import BaseModel, Field

class TransactionDetails(BaseModel):
    is_payment_receipt: bool = Field(
        default=False,
        description="True if the image shows a valid payment confirmation or receipt screen from GPay, PhonePe, Paytm, BHIM, or a bank."
    )
    amount: Optional[float] = Field(
        default=None,
        description="Exact numeric amount paid in INR (e.g., 250.00)."
    )
    currency: str = Field(default="INR", description="Currency, standard INR.")
    payee: Optional[str] = Field(
        default=None,
        description="Name of the person, merchant, store, or service who received the payment."
    )
    source_app: Optional[str] = Field(
        default="UPI",
        description="App used: GPay, PhonePe, Paytm, BHIM, or Other."
    )
    upi_ref_id: Optional[str] = Field(
        default=None,
        description="12-digit UPI reference number, UTR, or bank transaction ID."
    )
    date: Optional[str] = Field(
        default=None,
        description="Date of transaction formatted as DD-Mon-YYYY (e.g. 05-Oct-2026)."
    )
    time: Optional[str] = Field(
        default=None,
        description="Time of transaction formatted as HH:MM AM/PM (e.g. 11:30 AM)."
    )
    category: Optional[str] = Field(
        default=None,
        description="Category: Food, Travel, Sports, Shopping, Bills, Groceries, Entertainment, Health, or Other."
    )
    notes: Optional[str] = Field(
        default=None,
        description="Additional context, description, or notes derived from caption."
    )
    debited_account: Optional[str] = Field(
        default=None,
        description="Debited bank account and last 4 digits if shown (e.g. HDFC Bank **1234)."
    )


PROMPT_TEMPLATE = """You are a financial receipt parser specialized in Indian UPI and banking apps (Google Pay, PhonePe, Paytm, BHIM, Cred, and mobile banking apps).

Analyze the attached screenshot and extract the transaction details.

User Provided Caption / Notes: "{user_caption}"

Rules for extraction:
1. `is_payment_receipt`: Set to true ONLY if this screenshot confirms a completed/successful payment or debit. Set to false if it's an unrelated image, a pending request, or failure screen.
2. `amount`: Look for the primary paid amount. Must be a clean number (e.g. 1500.50). Remove currency symbols like ₹, Rs, INR.
3. `payee`: The merchant or recipient who received money (e.g. "Swiggy", "Decathlon", "Ramesh Kumar").
4. `source_app`: Identify whether it is Google Pay, PhonePe, Paytm, BHIM, or another app based on UI colors, logos, and fonts.
5. `upi_ref_id`: Look for "UPI transaction ID", "UPI Ref No", "UTR", or 12-digit reference number.
6. `date` and `time`: Extract the timestamp if visible. Standardize date to DD-Mon-YYYY and time to HH:MM AM/PM. If date is not shown, leave null.
7. `category`:
   - If the user's caption hints at a category (e.g. "food", "dinner", "cab", "travel", "sports", "badminton", "gym", "electricity"), prioritize that.
   - If no caption is given or caption is neutral, infer the category based on payee:
     * Food (restaurants, cafes, food delivery like Swiggy/Zomato, bakeries)
     * Travel (Uber, Ola, Rapido, flights, metro, fuel/petrol pumps)
     * Sports (Decathlon, turf bookings, gym, fitness equipment)
     * Groceries (Blinkit, Zepto, Instamart, supermarkets)
     * Shopping (Amazon, Flipkart, retail clothing stores)
     * Bills (Electricity, mobile recharge, Wi-Fi, water)
     * Health (Pharmacies, doctors, clinics)
     * Entertainment (BookMyShow, movies, games)
     * Other (Personal peer-to-peer transfers or unclassified)
8. `notes`: Use the user caption or brief detail about the item.
9. `debited_account`: Name of bank + last 4 digits if visible (e.g., "SBI **4821").

Return ONLY a valid JSON object matching the requested schema without any markdown formatting or surrounding explanation.
"""

import logging
import random
import time

logger = logging.getLogger("FinwatchVision")

# Candidate models in priority order (lite models provide high availability during flash load spikes)
FALLBACK_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-flash-latest",
]

RETRIABLE_STATUS_CODES = {429, 500, 502, 503, 504}

def parse_receipt_gemini(
    image_bytes: bytes,
    api_key: str,
    user_caption: str = "",
    mime_type: str = "image/jpeg",
    max_retries: int = 5,
    base_delay: float = 1.5
) -> TransactionDetails:
    """
    Parses a receipt image using Gemini Vision API with structured JSON output.
    Includes automated retry with exponential backoff and model rotation for retriable errors (503, 429, 500).
    """
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured.")

    prompt_text = PROMPT_TEMPLATE.format(user_caption=user_caption or "None provided")
    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": encoded_image
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.1
        }
    }

    last_error: Optional[Exception] = None

    for attempt in range(max_retries):
        model_name = FALLBACK_MODELS[attempt % len(FALLBACK_MODELS)]
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))

                candidates = resp_data.get("candidates", [])
                if not candidates:
                    return TransactionDetails(is_payment_receipt=False)

                content_parts = candidates[0].get("content", {}).get("parts", [])
                if not content_parts:
                    return TransactionDetails(is_payment_receipt=False)

                raw_json_str = content_parts[0].get("text", "{}")
                parsed_data = json.loads(raw_json_str)
                return TransactionDetails(**parsed_data)

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            last_error = RuntimeError(f"Gemini API request failed ({e.code}) on model '{model_name}': {error_body}")

            # Check if this status code is retriable
            if e.code in RETRIABLE_STATUS_CODES:
                if attempt < max_retries - 1:
                    delay = min(base_delay * (1.8 ** attempt) + random.uniform(0.5, 1.2), 12.0)
                    next_model = FALLBACK_MODELS[(attempt + 1) % len(FALLBACK_MODELS)]
                    logger.warning(
                        f"Gemini returned {e.code} ({e.reason}) on '{model_name}'. "
                        f"Retrying with '{next_model}' in {delay:.1f}s (attempt {attempt + 1}/{max_retries})..."
                    )
                    time.sleep(delay)
                    continue
            # If 404 on model name, try next model immediately
            elif e.code == 404:
                if attempt < max_retries - 1:
                    logger.info(f"Model '{model_name}' returned 404, falling back to next model...")
                    continue

            raise last_error

        except (urllib.error.URLError, TimeoutError) as e:
            last_error = e
            if attempt < max_retries - 1:
                delay = min(base_delay * (1.8 ** attempt) + random.uniform(0.5, 1.2), 12.0)
                logger.warning(f"Network error ({str(e)}) on model '{model_name}'. Retrying in {delay:.1f}s...")
                time.sleep(delay)
                continue
            raise RuntimeError(f"Network timeout contacting Gemini after {max_retries} attempts: {str(e)}")

        except Exception as e:
            raise RuntimeError(f"Failed to process receipt image: {str(e)}")

    if last_error:
        raise last_error
    raise RuntimeError("Failed to parse receipt after maximum retries.")
