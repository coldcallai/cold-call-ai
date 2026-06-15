"""MerchantBrain — Jargon Translation Map.

Per Funding V1 refinement: "Agent speaks business owner, not merchant services."

If a merchant says "What do you mean?" after the AI used any of these terms,
the engine auto-flags + replaces on the next attempt with the plain-English
equivalent.
"""
from __future__ import annotations


JARGON_MAP: dict[str, str] = {
    # merchant-services jargon -> business-owner language
    "settlement timing": "how quickly deposits hit your account",
    "settlement window": "when money becomes available in your account",
    "funding window": "when money becomes available",
    "funding cycle": "how often deposits hit your account",
    "batch processing": "how often payments get processed together",
    "batch cutoff": "the time of day payments get processed",
    "interchange": "the cost the card networks charge",
    "interchange-plus": "the cost the card networks charge plus a small markup",
    "pci compliance": "the security rules for handling card data",
    "pci": "the security rules for handling card data",
    "chargeback ratio": "how often customers dispute charges",
    "chargeback": "when a customer disputes a charge",
    "card-not-present": "payments taken online or over the phone",
    "card-not-present volume": "payments taken online or over the phone",
    "cnp volume": "payments taken online or over the phone",
    "card-present": "in-person payments",
    "payment acceptance workflow": "how customers usually pay you",
    "merchant of record": "the business that's legally on the receipt",
    "level 2 / level 3": "the extra data that lowers cost on business card payments",
    "level ii": "the extra data that lowers cost on business card payments",
    "level iii": "the extra data that lowers cost on business card payments",
    "downgrades": "when a transaction gets charged a higher rate than expected",
    "tokenization": "saving a card on file securely",
    "schedule a": "the page in the contract that lists your rates and fees",
    "residuals": "the share of fees passed back to your processor or referrer",
}
