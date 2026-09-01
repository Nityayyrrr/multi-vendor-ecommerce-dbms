"""
Master CLI Entry Point for Phase 3 ETL.
Executes the full pipeline:
1. Extract & Transform (data/raw/ -> data/processed/)
2. Pre-Load Dry Run Validation
3. MySQL 8.4 Schema Initialization (database/schema.sql)
4. 13-Stage Topological Batch Loading
5. Post-Load Live MySQL Validation Suite (27 checks)
"""
import sys
import time
import argparse

from etl.transform.pipeline import run_transformation_pipeline
from etl.validate.validate_etl import validate_dry_run_csvs, validate_mysql_database
from etl.load.db_connection import initialize_database_schema, get_connection
from etl.load.loader import execute_13_stage_load

def main():
    parser = argparse.ArgumentParser(description="Phase 3 ETL Pipeline for Multi-Vendor E-Commerce DBMS")
    parser.add_argument("--dry-run-only", action="store_true", help="Execute only transformation and dry-run validation without loading into MySQL")
    parser.add_argument("--skip-transform", action="store_true", help="Skip transformation and use existing processed CSVs")
    parser.add_argument("--validate-only", action="store_true", help="Run only the live MySQL validation suite")
    args = parser.parse_args()

    pipeline_start = time.time()
    print("================================================================================")
    print("PHASE 3: OLIST ETL, DATA TRANSFORMATION & MYSQL 8.4 POPULATION PIPELINE")
    print("================================================================================")

    if args.validate_only:
        print("[Mode: Live MySQL Validation Only]")
        conn = get_connection()
        try:
            success, errors = validate_mysql_database(conn)
            sys.exit(0 if success else 1)
        finally:
            conn.close()

    # Step 1: Extraction & Transformation
    if not args.skip_transform:
        print("\n>>> STEP 1: EXTRACT & TRANSFORM DATASETS <<<")
        datasets, metrics = run_transformation_pipeline()
    else:
        print("\n>>> STEP 1: SKIPPED (Using existing files in data/processed/) <<<")

    # Step 2: Pre-Load Dry Run Validation
    print("\n>>> STEP 2: PRE-LOAD DRY RUN VALIDATION <<<")
    dry_run_passed, dry_run_errors = validate_dry_run_csvs()
    if not dry_run_passed:
        print("\n[CRITICAL ERROR] Dry run validation failed. Aborting MySQL population.")
        sys.exit(1)

    if args.dry_run_only:
        print("\n[OK] Dry run completed successfully (--dry-run-only specified). Exiting without MySQL load.")
        sys.exit(0)

    # Step 3: MySQL 8.4 Schema Initialization
    print("\n>>> STEP 3: INITIALIZE MYSQL 8.4 DATABASE & SCHEMA <<<")
    initialize_database_schema()

    # Step 4: 13-Stage Topological MySQL Loading
    print("\n>>> STEP 4: 13-STAGE TOPOLOGICAL MYSQL BATCH LOADING <<<")
    loaded_counts = execute_13_stage_load()

    # Step 5: Post-Load Live Validation
    print("\n>>> STEP 5: POST-LOAD LIVE MYSQL VALIDATION SUITE <<<")
    conn = get_connection()
    try:
        live_passed, live_errors = validate_mysql_database(conn)
        if not live_passed:
            print("\n[CRITICAL ERROR] Live MySQL database validation failed.")
            sys.exit(1)
    finally:
        conn.close()

    total_pipeline_time = round(time.time() - pipeline_start, 2)
    print("================================================================================")
    print(f"PHASE 3 ETL PIPELINE COMPLETED SUCCESSFULLY IN {total_pipeline_time}s")
    print("================================================================================")

if __name__ == "__main__":
    main()
