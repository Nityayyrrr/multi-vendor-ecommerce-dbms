"""
Database Connection and DDL Execution Manager for MySQL 8.4.
Uses PyMySQL with explicit transaction controls and parameterized queries.
"""
import os
import pymysql
from typing import Optional, Dict, Any

from etl.config import DB_CONFIG, DATABASE_DIR

def get_connection(db_name: Optional[str] = None, autocommit: bool = False):
    """
    Establishes and returns a PyMySQL connection.
    """
    config = dict(DB_CONFIG)
    if db_name is not None:
        config["database"] = db_name
    config["autocommit"] = autocommit
    return pymysql.connect(**config)

def initialize_database_schema(schema_sql_path: Optional[str] = None) -> bool:
    """
    Creates database if not exists and executes schema.sql to establish canonical 12 tables.
    """
    if schema_sql_path is None:
        schema_sql_path = str(DATABASE_DIR / "schema.sql")

    print("--- Initializing MySQL 8.4 Database and Schema ---")
    
    # 1. Connect without specific DB to create database
    root_config = dict(DB_CONFIG)
    root_config.pop("database", None)
    root_config["autocommit"] = True
    
    conn = pymysql.connect(**root_config)
    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    conn.close()

    # 2. Connect to the target DB and execute schema.sql statements
    conn = get_connection(autocommit=False)
    with open(schema_sql_path, "r", encoding="utf-8") as f:
        sql_script = f.read()

    # Split SQL script on semicolon, preserving table definitions
    statements = [s.strip() for s in sql_script.split(";") if s.strip()]
    with conn.cursor() as cur:
        # Disable foreign key checks for clean DDL execution
        cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
        for stmt in statements:
            if stmt:
                cur.execute(stmt)
        cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
    conn.commit()
    conn.close()

    print(f"  [OK] Successfully executed {len(statements)} DDL statements against `{DB_CONFIG['database']}`.")
    return True
