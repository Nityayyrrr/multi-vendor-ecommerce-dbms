"""
Transform Vendors entity.
Canonical Target Table:
- VENDOR (vendor_id = seller_id)
Attributes:
- vendor_id: DIRECT (seller_id)
- vendor_name: SYNTHETIC/AUGMENTED (deterministic commercial merchant name)
- rating: DERIVED (mathematical average of review scores linked to seller orders, default 5.00)
- gst_number: SYNTHETIC/AUGMENTED (deterministic unique GST string GST-<STATE>-<HEX8>)
"""
import csv
import hashlib
from collections import defaultdict
from typing import Dict, List, Any

def transform_vendors(
    raw_sellers_path: str,
    raw_items_path: str,
    raw_reviews_path: str
) -> List[Dict[str, Any]]:
    """
    Transforms raw seller data, reviews, and items into canonical VENDOR records.
    """
    # 1. Map order_id -> set of seller_ids
    order_to_sellers: Dict[str, set] = defaultdict(set)
    with open(raw_items_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            order_to_sellers[r["order_id"]].add(r["seller_id"])

    # 2. Map seller_id -> list of review scores
    seller_review_scores: Dict[str, List[float]] = defaultdict(list)
    with open(raw_reviews_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            oid = r["order_id"]
            score_str = r.get("review_score", "")
            if score_str:
                try:
                    score = float(score_str)
                    for sid in order_to_sellers.get(oid, set()):
                        seller_review_scores[sid].append(score)
                except ValueError:
                    pass

    # 3. Read sellers dataset and build VENDOR records
    vendor_records: List[Dict[str, Any]] = []
    seen_gst_numbers = set()

    with open(raw_sellers_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            sid = r["seller_id"].strip()
            city = r["seller_city"].strip().title()
            state = r["seller_state"].strip().upper()

            # Calculate derived rating
            if sid in seller_review_scores and len(seller_review_scores[sid]) > 0:
                avg_score = sum(seller_review_scores[sid]) / len(seller_review_scores[sid])
                rating = round(avg_score, 2)
                # Bound between 1.00 and 5.00
                rating = max(1.00, min(5.00, rating))
            else:
                rating = 5.00

            # Deterministic vendor name
            vendor_name = f"{city} Merchant {sid[:6].upper()}"

            # Deterministic unique GST Number
            h = hashlib.md5(f"gst_{sid}".encode("utf-8")).hexdigest()[:8].upper()
            gst_number = f"GST-{state}-{h}"
            
            # Ensure 100% uniqueness
            if gst_number in seen_gst_numbers:
                h_alt = hashlib.sha256(f"gst_{sid}".encode("utf-8")).hexdigest()[:8].upper()
                gst_number = f"GST-{state}-{h_alt}"
            seen_gst_numbers.add(gst_number)

            vendor_records.append({
                "vendor_id": sid,
                "vendor_name": vendor_name,
                "rating": rating,
                "gst_number": gst_number
            })

    return vendor_records
