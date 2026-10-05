"""
Builds the CATEGORY hierarchy, PRODUCT catalog, and PRODUCT_TAG keywords
from Olist's products + translations CSVs.
"""
import csv
import statistics
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Optional

# The 9 top-level root categories
L1_ROOT_CATEGORIES = [
    (1, "Electronics & Appliances"),
    (2, "Home & Furniture"),
    (3, "Fashion & Accessories"),
    (4, "Health & Beauty"),
    (5, "Sports, Hobbies & Leisure"),
    (6, "Automotive & Industry"),
    (7, "Food & Beverages"),
    (8, "Pet Care"),
    (9, "Stationery, Gifts & Misc"),
]

# Two categories Olist's translation file is missing
MANUAL_TRANSLATIONS = {
    "pc_gamer": "PC Gaming",
    "portateis_cozinha_e_preparadores_de_alimentos": "Kitchen & Food Appliances"
}

# Which root category each subcategory slug belongs under
L2_TO_L1_PARENT_MAP = {
    # 1. Electronics & Appliances
    "audio": 1, "cinem_photo": 1, "cine_photo": 1, "cine_foto": 1, "computers": 1, "pcs": 1,
    "computers_accessories": 1, "informatica_acessorios": 1, "electronics": 1, "eletronicos": 1,
    "home_appliances": 1, "eletrodomesticos": 1, "home_appliances_2": 1, "eletrodomesticos_2": 1,
    "small_appliances": 1, "eletroportateis": 1, "tablets_printing_image": 1, "tablets_impressao_imagem": 1,
    "telephony": 1, "telefonia": 1, "fixed_telephony": 1, "telefonia_fixa": 1,
    "pc_gamer": 1, "portateis_cozinha_e_preparadores_de_alimentos": 1,
    "consoles_games": 1, "small_appliances_home_oven_and_coffee": 1, "portateis_casa_forno_e_cafe": 1,

    # 2. Home & Furniture
    "bed_bath_table": 2, "cama_mesa_banho": 2, "furniture_bedroom": 2, "moveis_quarto": 2,
    "furniture_decor": 2, "moveis_decoracao": 2, "furniture_living_room": 2, "moveis_sala": 2,
    "furniture_mattress_and_upholstery": 2, "moveis_colchao_e_estofado": 2,
    "kitchen_dining_laundry_garden_furniture": 2, "moveis_cozinha_area_de_servico_jantar_e_jardim": 2,
    "office_furniture": 2, "moveis_escritorio": 2, "home_comfort": 2, "home_confort": 2, "casa_conforto": 2,
    "home_comfort_2": 2, "casa_conforto_2": 2, "home_construction": 2, "casa_construcao": 2,
    "housewares": 2, "utilidades_domesticas": 2, "air_conditioning": 2, "climatizacao": 2,
    "la_cuisine": 2, "flowers": 2, "flores": 2,

    # 3. Fashion & Accessories
    "fashion_bags_accessories": 3, "fashion_bolsas_e_acessorios": 3,
    "fashion_childrens_clothes": 3, "fashion_roupa_infanto_juvenil": 3,
    "fashion_female_clothing": 3, "fashio_female_clothing": 3, "fashion_roupa_feminina": 3,
    "fashion_male_clothing": 3, "fashion_roupa_masculina": 3,
    "fashion_shoes": 3, "fashion_calcados": 3,
    "fashion_sport": 3, "fashion_esporte": 3,
    "fashion_underwear_beach": 3, "fashion_underwear_e_moda_praia": 3,
    "luggage_accessories": 3, "malas_acessorios": 3,
    "watches_gifts": 3, "relogios_presentes": 3,

    # 4. Health & Beauty
    "health_beauty": 4, "beleza_saude": 4, "perfumery": 4, "perfumaria": 4,
    "diapers_and_hygiene": 4, "fraldas_higiene": 4,

    # 5. Sports, Hobbies & Leisure
    "sports_leisure": 5, "esporte_lazer": 5, "musical_instruments": 5, "instrumentos_musicais": 5,
    "music": 5, "musica": 5, "toys": 5, "brinquedos": 5, "baby": 5, "bebes": 5,
    "books_general_interest": 5, "livros_interesse_geral": 5,
    "books_imported": 5, "livros_importados": 5,
    "books_technical": 5, "livros_tecnicos": 5,
    "cds_dvds_musicals": 5, "cds_dvds_musicais": 5,
    "dvds_blu_ray": 5, "arts_and_craftmanship": 5, "artes_e_artesanato": 5,
    "art": 5, "artes": 5, "party_supplies": 5, "artigos_de_festas": 5,
    "christmas_supplies": 5, "artigos_de_natal": 5,

    # 6. Automotive & Industry
    "auto": 6, "automotivo": 6,
    "construction_tools_construction": 6, "construcao_ferramentas_construcao": 6,
    "construction_tools_garden": 6, "costruction_tools_garden": 6, "construcao_ferramentas_jardim": 6,
    "construction_tools_lights": 6, "construcao_ferramentas_iluminacao": 6,
    "construction_tools_safety": 6, "construcao_ferramentas_seguranca": 6,
    "costruction_tools_tools": 6, "construcao_ferramentas_ferramentas": 6,
    "garden_tools": 6, "ferramentas_jardim": 6,
    "industry_commerce_and_business": 6, "industria_comercio_e_negocios": 6,
    "agro_industry_and_commerce": 6, "agro_industria_e_comercio": 6,
    "security_and_services": 6, "seguros_e_servicos": 6,
    "signaling_and_security": 6, "sinalizacao_e_seguranca": 6,

    # 7. Food & Beverages
    "food": 7, "alimentos": 7, "food_drink": 7, "alimentos_bebidas": 7, "drinks": 7, "bebidas": 7,

    # 8. Pet Care
    "pet_shop": 8,

    # 9. Stationery, Gifts & Misc
    "stationery": 9, "papelaria": 9, "cool_stuff": 9, "market_place": 9,
    "general_merchandise_uncategorized": 9
}

def format_category_display_name(english_slug: str) -> str:
    """Turn an English slug like 'home_appliances' into 'Home Appliances'."""
    words = english_slug.replace("_", " ").split()
    return " ".join([w.capitalize() if w.lower() not in ["and", "e", "de", "of", "&"] else "&" for w in words])

def build_category_hierarchy(
    raw_translations_path: str,
    raw_products_path: str
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Build the 2-level category tree (9 roots + subcategories + 1 fallback).
    Returns (category_records, slug_to_id_map).
    """
    # Load translations (utf-8-sig handles BOM if present)
    translations: Dict[str, str] = {}
    with open(raw_translations_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            port_name = r["product_category_name"].strip()
            eng_name = r["product_category_name_english"].strip()
            translations[port_name] = eng_name

    # Add manual translations for known missing slugs
    for k, v in MANUAL_TRANSLATIONS.items():
        translations[k] = v

    # Root categories
    category_records: List[Dict[str, Any]] = []
    for cid, cname in L1_ROOT_CATEGORIES:
        category_records.append({
            "category_id": cid,
            "category_name": cname,
            "parent_category_id": None
        })

    # Subcategories
    port_to_cat_id: Dict[str, int] = {}
    next_id = 10
    
    # Sort so IDs stay deterministic
    sorted_slugs = sorted(translations.keys())
    for port_slug in sorted_slugs:
        eng_raw = translations[port_slug]
        display_name = format_category_display_name(eng_raw) if port_slug not in MANUAL_TRANSLATIONS else MANUAL_TRANSLATIONS[port_slug]
        parent_id = L2_TO_L1_PARENT_MAP.get(port_slug, L2_TO_L1_PARENT_MAP.get(eng_raw, 9))

        category_records.append({
            "category_id": next_id,
            "category_name": display_name,
            "parent_category_id": parent_id
        })
        port_to_cat_id[port_slug] = next_id
        next_id += 1

    # Fallback category for products without one
    fallback_cat_id = next_id
    fallback_name = "General Merchandise / Uncategorized"
    category_records.append({
        "category_id": fallback_cat_id,
        "category_name": fallback_name,
        "parent_category_id": 9 # under Stationery, Gifts & Misc
    })
    port_to_cat_id[""] = fallback_cat_id
    port_to_cat_id[None] = fallback_cat_id

    return category_records, port_to_cat_id

def transform_catalog(
    raw_products_path: str,
    raw_items_path: str,
    raw_orders_path: str,
    raw_translations_path: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Main entry point — returns (categories, products, tags).
    """
    # Build categories
    category_records, port_to_cat_id = build_category_hierarchy(raw_translations_path, raw_products_path)
    cat_id_to_name = {c["category_id"]: c["category_name"] for c in category_records}

    # Read order timestamps
    order_timestamps: Dict[str, str] = {}
    with open(raw_orders_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            order_timestamps[r["order_id"]] = r["order_purchase_timestamp"]

    # Track sales volume and prices from order items
    product_seller_stats: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(
        lambda: defaultdict(lambda: {"volume": 0, "earliest_ts": "9999-99-99 99:99:99"})
    )
    product_historical_prices: Dict[str, List[float]] = defaultdict(list)
    product_sales_volume: Dict[str, int] = defaultdict(int)

    with open(raw_items_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            pid = r["product_id"].strip()
            sid = r["seller_id"].strip()
            oid = r["order_id"].strip()
            price = float(r["price"])
            ots = order_timestamps.get(oid, "2018-01-01 00:00:00")

            product_seller_stats[pid][sid]["volume"] += 1
            if ots < product_seller_stats[pid][sid]["earliest_ts"]:
                product_seller_stats[pid][sid]["earliest_ts"] = ots

            product_historical_prices[pid].append(price)
            product_sales_volume[pid] += 1

    # Pick primary vendor (most sales, earliest sale, or lower ID)
    product_primary_vendor: Dict[str, str] = {}
    for pid, sellers_map in product_seller_stats.items():
        # Sort by: 1. volume DESC, 2. earliest_ts ASC, 3. seller_id ASC
        sorted_candidates = sorted(
            sellers_map.items(),
            key=lambda item: (-item[1]["volume"], item[1]["earliest_ts"], item[0])
        )
        product_primary_vendor[pid] = sorted_candidates[0][0]

    # Build product and tag rows
    product_records: List[Dict[str, Any]] = []
    product_tag_records: List[Dict[str, Any]] = []

    with open(raw_products_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            pid = r["product_id"].strip()
            raw_cat = r["product_category_name"].strip() if r["product_category_name"] else ""
            cat_id = port_to_cat_id.get(raw_cat, port_to_cat_id[""])
            cat_name = cat_id_to_name.get(cat_id, "General Merchandise")

            # Use median historical price, fallback to 100.00
            prices = product_historical_prices.get(pid, [100.00])
            catalog_price = round(statistics.median(prices), 2)

            # Primary Vendor
            vendor_id = product_primary_vendor.get(pid)
            if not vendor_id:
                # Fallback to first seller if none found
                vendor_id = "0015a82c2db000afd65372437fb4f079"

            # Product Name & Description
            p_name = f"{cat_name} Product #{pid[:6].upper()}"
            weight_g = r.get("product_weight_g") or "500"
            len_cm = r.get("product_length_cm") or "20"
            height_cm = r.get("product_height_cm") or "20"
            width_cm = r.get("product_width_cm") or "20"
            description = (
                f"Standard catalog item in {cat_name}. "
                f"Package dimensions: {len_cm}x{width_cm}x{height_cm} cm, Weight: {weight_g}g."
            )

            product_records.append({
                "product_id": pid,
                "product_name": p_name[:150],
                "description": description,
                "price": catalog_price,
                "category_id": cat_id,
                "vendor_id": vendor_id,
                "status": "Active"
            })

            # Generate tags
            tags = set()
            # Category keyword tag
            first_cat_token = cat_name.lower().replace("&", "").split()[0]
            if len(first_cat_token) >= 2:
                tags.add(first_cat_token)

            # Price tier tag
            if catalog_price < 50.00:
                tags.add("budget")
            elif catalog_price <= 250.00:
                tags.add("midrange")
            else:
                tags.add("premium")

            # Popularity tag
            sales = product_sales_volume.get(pid, 0)
            if sales >= 10:
                tags.add("bestseller")
            elif sales >= 3:
                tags.add("popular")
            else:
                tags.add("standard")

            for t in sorted(tags):
                product_tag_records.append({
                    "product_id": pid,
                    "tag": t
                })

    return category_records, product_records, product_tag_records
