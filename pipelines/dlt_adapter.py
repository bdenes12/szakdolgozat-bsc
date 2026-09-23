import os
import dlt
from dlt.sources.sql_database import sql_database
from dotenv import load_dotenv

def prod_to_staging():

    load_dotenv()

    prod_dsn = None
    staging_dsn = None

    prod_dsn = os.getenv("PRODUCTION_DSN")
    staging_dsn = os.getenv("STAGING_DSN")

    if prod_dsn is None or staging_dsn is None:
        raise ValueError(f"Hiányzik a PRODUCTION_DSN vagy a STAGING_DSN !")

    source = sql_database(
        prod_dsn,
        schema="public",
        backend="pyarrow"
    )

    pipeline = dlt.pipeline(
        pipeline_name="prod_to_staging",
        destination="postgres",
        dataset_name="public"
    )

    pipeline.run(source, credentials=staging_dsn, write_disposition="replace")

def staging_to_dev():

    load_dotenv()

    staging_dsn = None
    dev_dsn = None

    staging_dsn = os.getenv("STAGING_DSN")
    dev_dsn = os.getenv("DEV_DSN")

    if dev_dsn is None or staging_dsn is None:
        raise ValueError(f"Hiányzik a DEV_DSN vagy a STAGING_DSN !")

    source = sql_database(
        staging_dsn,
        schema="dev_export",
        table_names=["departments"],
        backend="pyarrow"
    )

    pipeline = dlt.pipeline(
        pipeline_name="staging_to_dev",
        destination="postgres",
        dataset_name="public"
    )

    pipeline.run(source, credentials=dev_dsn, write_disposition="replace")