"""Configuration for Spokane Public Brief v2 (serverless)."""

import os


class Settings:
    """Settings from environment variables (Lambda-friendly, no .env files)."""

    @property
    def stage(self) -> str:
        return os.environ.get("STAGE", "local")

    @property
    def meetings_table(self) -> str:
        return os.environ.get("MEETINGS_TABLE", "spokane-public-brief-meetings-local")

    @property
    def agenda_table(self) -> str:
        return os.environ.get("AGENDA_TABLE", "spokane-public-brief-agenda-items-local")

    @property
    def documents_table(self) -> str:
        return os.environ.get("DOCUMENTS_TABLE", "spokane-public-brief-documents-local")

    @property
    def ingest_queue_url(self) -> str:
        return os.environ.get("INGEST_QUEUE_URL", "")

    @property
    def aws_region(self) -> str:
        return os.environ.get("AWS_REGION", "us-west-2")

    @property
    def legistar_base_url(self) -> str:
        return "https://webapi.legistar.com/v1/spokane"

    @property
    def debug(self) -> bool:
        return os.environ.get("DEBUG", "false").lower() == "true"


settings = Settings()
