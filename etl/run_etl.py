"""
Main entry point for the ETL pipeline.
Runs transform -> dry-run check -> schema init -> load -> validate,
or a subset depending on the CLI flags.
"""
import os
import sys
import time
import argparse

# Ensure repository root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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
    print("Starting ETL pipeline...")

    if args.validate_only:
        print("Running database validation only...")
        conn = get_connection()
        try:
            success, errors = validate_mysql_database(conn)
            sys.exit(0 if success else 1)
        finally:
            conn.close()

    # step 1: transform
    if not args.skip_transform:
        print("\nStep 1: Transforming data...")
        datasets, metrics = run_transformation_pipeline()
    else:
        print("\nStep 1: Skipped transform (using existing data/processed/ CSVs)")

    # step 2: dry-run validation
    print("Step 2: Validating processed files...")
    dry_run_passed, dry_run_errors = validate_dry_run_csvs()
    if not dry_run_passed:
        print("\nDry run validation failed. Stopping before database load.")
        sys.exit(1)

    if args.dry_run_only:
        print("Dry run finished (--dry-run-only specified). Exiting.")
        sys.exit(0)

    # step 3: schema init
    print("Step 3: Initializing database schema...")
    initialize_database_schema()

    # step 4: load
    print("Step 4: Loading data into MySQL...")
    loaded_counts = execute_13_stage_load()

    # step 5: live validation
    print("Step 5: Validating database...")
    conn = get_connection()
    try:
        live_passed, live_errors = validate_mysql_database(conn)
        if not live_passed:
            print("\nDatabase validation failed.")
            sys.exit(1)
    finally:
        conn.close()

    total_pipeline_time = round(time.time() - pipeline_start, 2)
    print(f"\nPipeline finished in {total_pipeline_time}s.")

if __name__ == "__main__":
    main()
