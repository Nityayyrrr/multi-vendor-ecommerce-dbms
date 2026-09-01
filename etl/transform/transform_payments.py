"""
Transform Payment Entity.
Canonical Target Table:
- PAYMENT (Composite PK: order_id, payment_id, FK -> orders)
Attributes:
- order_id: DIRECT (FK -> orders.order_id)
- payment_id: DIRECT (payment_sequential)
- amount: DERIVED (payment_value; 9 zero-values explicitly sanitized to 0.01)
- mode: DERIVED (payment_type)
- status: DERIVED ('Success' / 'Refunded')
- payment_date: DERIVED (order_approved_at / order_purchase_timestamp)
- transaction_reference: SYNTHETIC/AUGMENTED (deterministic unique MD5 string)
"""
import csv
import hashlib
from typing import Dict, List, Tuple, Any

def transform_payments(
    raw_payments_path: str,
    raw_orders_path: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Transforms raw payments dataset into canonical PAYMENT records.
    Returns:
        (payment_records, sanitized_zero_payment_logs)
    """
    # 1. Map order_id -> {payment_date, status}
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

    # 2. Read and transform PAYMENT records
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

            # Sanitize 0.00 payments to 0.01 to meet target schema check constraint `chk_payment_amount: amount > 0.00`
            if raw_val <= 0.00:
                amount = 0.01
                sanitized_logs.append({
                    "order_id": oid,
                    "payment_sequential": seq,
                    "original_value": raw_val,
                    "sanitized_value": amount,
                    "mode": mode,
                    "reason": "Sanitized to 0.01 to satisfy MySQL check constraint chk_payment_amount (amount > 0.00)"
                })
            else:
                amount = raw_val

            # Payment Date and Status
            o_data = order_info.get(oid, {"payment_date": "2018-01-01 00:00:00", "order_status": "delivered"})
            p_date = o_data["payment_date"]
            if o_data["order_status"] == "canceled" and mode == "voucher":
                p_status = "Refunded"
            else:
                p_status = "Success"

            # Deterministic unique transaction reference
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
