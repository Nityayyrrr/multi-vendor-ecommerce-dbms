"""
Builds the PAYMENT table from Olist's order_payments CSV.
The 9 zero-value payments get bumped to 0.01 so they pass the
check constraint (amount > 0.00). Each payment gets a unique
transaction reference hash.
"""
import csv
import hashlib
from typing import Dict, List, Tuple, Any

def transform_payments(
    raw_payments_path: str,
    raw_orders_path: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Returns (payment_records, list_of_sanitized_zero_payments).
    """
    # Map order ID to date and status
    order_info: Dict[str, Dict[str, str]] = {}
    with open(raw_orders_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            oid = r["order_id"].strip()
            app_at = r["order_approved_at"].strip()
            purch_at = r["order_purchase_timestamp"].strip()
            status = r["order_status"].strip().lower()
            p_date = app_at if app_at else purch_at
            order_info[oid] = {
                "payment_date": p_date,
                "order_status": status
            }

    # Build payment rows
    payment_records: List[Dict[str, Any]] = []
    sanitized_logs: List[Dict[str, Any]] = []
    seen_txn_refs = set()

    with open(raw_payments_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            oid = r["order_id"].strip()
            seq = int(r["payment_sequential"].strip())
            raw_val = float(r["payment_value"].strip())
            mode = r["payment_type"].strip()

            # Bump 0.00 to 0.01 so it passes amount > 0 check constraint
            if raw_val <= 0.00:
                amount = 0.01
                sanitized_logs.append({
                    "order_id": oid,
                    "payment_sequential": seq,
                    "original_value": raw_val,
                    "sanitized_value": amount,
                    "mode": mode,
                    "reason": "Bumped to 0.01 to satisfy chk_payment_amount"
                })
            else:
                amount = raw_val

            # Date and status
            o_data = order_info.get(oid, {"payment_date": "2018-01-01 00:00:00", "order_status": "delivered"})
            p_date = o_data["payment_date"]
            if o_data["order_status"] == "canceled" and mode == "voucher":
                p_status = "Refunded"
            else:
                p_status = "Success"

            # Transaction reference
            h = hashlib.md5(f"txn_{oid}_{seq}".encode("utf-8")).hexdigest()[:16].upper()
            txn_ref = f"TXN-{h}"
            if txn_ref in seen_txn_refs:
                h_alt = hashlib.sha256(f"txn_{oid}_{seq}".encode("utf-8")).hexdigest()[:16].upper()
                txn_ref = f"TXN-{h_alt}"
            seen_txn_refs.add(txn_ref)

            payment_records.append({
                "order_id": oid,
                "payment_id": seq,
                "amount": amount,
                "mode": mode,
                "status": p_status,
                "payment_date": p_date,
                "transaction_reference": txn_ref
            })

    return payment_records, sanitized_logs
