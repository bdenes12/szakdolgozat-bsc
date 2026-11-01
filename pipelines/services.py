import psycopg2
from dlt.pipeline.exceptions import PipelineStepFailed
from sqlalchemy.exc import OperationalError as SQLAlchemyOperationalError

from anonymization.services import run_full_anonymization
from config.logger import setup_logger
from validations.services import ValidationService

from .dlt_adapter import prod_to_staging, staging_to_dev
from .models import PipelineRun

logger = setup_logger("pipelines", console=False)


class PipelineService:
    def __init__(
        self,
        transfer_to_staging=prod_to_staging,
        transfer_to_dev=staging_to_dev,
        anonymize=run_full_anonymization,
        validation_service=None,
    ):
        self.transfer_to_staging = transfer_to_staging
        self.transfer_to_dev = transfer_to_dev
        self.anonymize = anonymize
        self.validation_service = validation_service or ValidationService()

    def start_pipeline(self):
        pipeline_run = PipelineRun.objects.create(status=PipelineRun.RunStatuses.RUNNING)

        logger.info(f"Pipeline futás elindult - pipeline_id: {pipeline_run.id}")
        step = "Indítás"

        try:
            step = "PROD -> STAGING"
            self.transfer_to_staging()
            logger.info(f"A PROD adatok STAGING-ba történő áttöltése kész - pipeline_id: {pipeline_run.id}")

            step = "Anonimizálás"
            logger.info("Anonimizálás elindult")
            self.anonymize()
            logger.info("Anonimizálás kész")

            step = "STAGING -> DEV"
            self.transfer_to_dev()
            logger.info(f"A maszkolt adatok STAGING -> DEV áttöltése kész - pipeline_id: {pipeline_run.id}")

            step = "Validáció"
            self.validation_service.run_validation(pipeline_run)

            pipeline_run.mark_completed()
            logger.info(f"Pipeline futás kész - pipeline_id: {pipeline_run.id}")

            return pipeline_run

        except (psycopg2.OperationalError, SQLAlchemyOperationalError):
            logger.error(f"Adatbázis nem érhető el - pipeline_id: {pipeline_run.id}, lépés: {step}")
            pipeline_run.mark_failed(f"Adatbázis nem érhető el ({step})")

            return pipeline_run

        except PipelineStepFailed:
            logger.error(f"Sikertelen áttöltés - pipeline_id: {pipeline_run.id}, lépés: {step}")
            pipeline_run.mark_failed(f"Sikertelen áttöltés ({step})")

            return pipeline_run

        except Exception as e:
            logger.error(
                f"Pipeline futás sikertelen - pipeline_id: {pipeline_run.id}, lépés: {step}, hiba típusa: {type(e).__name__}"
            )
            pipeline_run.mark_failed(err_message=f"Sikertelen lépés: {step}")

            return pipeline_run
