"""
Transform Customers, Customer Phone, and Address entities.
Canonical Target Tables:
- CUSTOMER (customer_id = customer_unique_id)
- CUSTOMER_PHONE (Composite PK: customer_id, phone_number) [100% SYNTHETIC/AUGMENTED]
- ADDRESS (Composite PK: customer_id, address_type) [DIRECT/DERIVED/SYNTHETIC STREET]
"""
import csv
import hashlib
from collections import defaultdict
from typing import Dict, List, Tuple, Any

# Standard Brazilian State DDD area codes for phone number synthesis
STATE_DDD_MAP = {
    "SP": "11", "RJ": "21", "ES": "27", "MG": "31", "PR": "41", "SC": "48", "RS": "51",
    "MS": "67", "MT": "65", "GO": "62", "DF": "61", "BA": "71", "SE": "79", "AL": "82",
    "PE": "81", "PB": "83", "RN": "84", "CE": "85", "PI": "86", "MA": "98", "PA": "91",
    "AP": "96", "AM": "92", "RR": "95", "AC": "68", "RO": "69", "TO": "63"
}

# Deterministic name generator components
FIRST_NAMES = [
    "Lucas", "Gabriel", "Mateus", "Rodrigo", "Leonardo", "Bruno", "Eduardo", "Felipe",
    "Thiago", "Guilherme", "Rafael", "Gustavo", "Marcelo", "Andre", "Juliana", "Mariana",
    "Beatriz", "Camila", "Larissa", "Fernanda", "Amanda", "Letícia", "Carolina", "Patricia",
    "Aline", "Bruna", "Renata", "Jessica", "Vanessa", "Paula", "Diego", "Alexandre"
]

LAST_NAMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira",
    "Lima", "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho", "Almeida", "Lopes",
    "Soares", "Fernandes", "Vieira", "Barbosa", "Rocha", "Dias", "Nascimento", "Andrade",
    "Moreira", "Nunes", "Marques", "Machado", "Mendes", "Freitas", "Cardoso", "Ramos"
]

def generate_deterministic_name(uid: str) -> str:
    """Deterministically generates a Brazilian human name from customer_unique_id hash."""
    h = int(hashlib.md5(uid.encode("utf-8")).hexdigest(), 16)
    fn = FIRST_NAMES[h % len(FIRST_NAMES)]
    ln1 = LAST_NAMES[(h // len(FIRST_NAMES)) % len(LAST_NAMES)]
    ln2 = LAST_NAMES[(h // (len(FIRST_NAMES) * len(LAST_NAMES))) % len(LAST_NAMES)]
    return f"{fn} {ln1} {ln2}" if ln1 != ln2 else f"{fn} {ln1} Silveira"

def generate_deterministic_phone(uid: str, state: str) -> str:
    """Deterministically synthesizes an E.164 Brazilian mobile phone number (+55 <DDD> 9<8-digits>)."""
    ddd = STATE_DDD_MAP.get(state.upper(), "11")
    h = int(hashlib.md5(f"phone_{uid}".encode("utf-8")).hexdigest()[:8], 16)
    num_part = str(h % 100000000).zfill(8)
    return f"+55{ddd}9{num_part}"

def generate_deterministic_street(uid: str) -> str:
    """Generates an honest synthetic street address acknowledging lack of street in Olist."""
    h = int(hashlib.md5(f"street_{uid}".encode("utf-8")).hexdigest()[:6], 16)
    prefix = uid[:6].upper()
    suite = (h % 900) + 100
    return f"Synthetic Street {prefix}, Suite {suite}"

def transform_customers_and_addresses(
    raw_customers_path: str,
    raw_orders_path: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Extracts and transforms CUSTOMER, CUSTOMER_PHONE, and ADDRESS.
    Returns:
        (customers_records, customer_phone_records, address_records)
    """
    # 1. Map raw order dates to customer tokens
    # customer_id (order token) -> {earliest_date, latest_date}
    cust_token_to_unique: Dict[str, str] = {}
    unique_cust_orders: Dict[str, List[str]] = defaultdict(list)
    
    # Read raw customers dataset
    raw_cust_rows: List[Dict[str, str]] = []
    with open(raw_customers_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_cust_rows.append(row)
            cid = row["customer_id"]
            uid = row["customer_unique_id"]
            cust_token_to_unique[cid] = uid

    # Read raw orders dataset to find earliest and latest order timestamps per customer_unique_id
    cust_earliest_date: Dict[str, str] = {}
    cust_latest_order_token: Dict[str, Tuple[str, str]] = {} # uid -> (latest_date, customer_id_token)

    with open(raw_orders_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["customer_id"]
            dt = row["order_purchase_timestamp"]
            uid = cust_token_to_unique.get(cid)
            if uid:
                # Earliest order purchase date -> customer.join_date
                if uid not in cust_earliest_date or dt < cust_earliest_date[uid]:
                    cust_earliest_date[uid] = dt
                # Latest order -> for picking the latest delivery address
                if uid not in cust_latest_order_token or dt > cust_latest_order_token[uid][0]:
                    cust_latest_order_token[uid] = (dt, cid)

    # 2. Build unique CUSTOMER entities
    # For address data, we prioritize the latest order token's address
    unique_customers: Dict[str, Dict[str, Any]] = {}
    for row in raw_cust_rows:
        cid = row["customer_id"]
        uid = row["customer_unique_id"]
        
        # If this is the latest token or the first time seeing this uid
        is_latest = (uid in cust_latest_order_token and cust_latest_order_token[uid][1] == cid) or (uid not in unique_customers)
        
        if is_latest or uid not in unique_customers:
            unique_customers[uid] = {
                "customer_id": uid,
                "city": row["customer_city"].strip().title(),
                "state": row["customer_state"].strip().upper(),
                "zip_code_prefix": row["customer_zip_code_prefix"].strip(),
            }

    customer_records: List[Dict[str, Any]] = []
    phone_records: List[Dict[str, Any]] = []
    address_records: List[Dict[str, Any]] = []

    for uid, cdata in unique_customers.items():
        join_date = cust_earliest_date.get(uid, "2016-09-04 21:15:19")
        email = f"customer_{uid[:12]}@ecommerce-demo.com"
        name = generate_deterministic_name(uid)
        
        # 1. CUSTOMER record
        customer_records.append({
            "customer_id": uid,
            "name": name,
            "email": email,
            "join_date": join_date
        })

        # 2. CUSTOMER_PHONE record (100% Synthetic/Augmented)
        phone_number = generate_deterministic_phone(uid, cdata["state"])
        phone_records.append({
            "customer_id": uid,
            "phone_number": phone_number,
            "phone_type": "Mobile"
        })

        # 3. ADDRESS record
        street = generate_deterministic_street(uid)
        pincode = f"{cdata['zip_code_prefix']}-000"
        address_records.append({
            "customer_id": uid,
            "address_type": "Shipping",
            "street": street,
            "city": cdata["city"],
            "state": cdata["state"],
            "pincode": pincode,
            "is_default": 1
        })

    return customer_records, phone_records, address_records
