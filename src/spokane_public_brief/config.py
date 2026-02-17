"""Configuration for Spokane Public Brief v2 (serverless)."""

import os

import boto3


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
    def dynamodb_endpoint(self) -> str | None:
        """DynamoDB endpoint URL override for local development."""
        return os.environ.get("DYNAMODB_ENDPOINT")

    @property
    def legistar_base_url(self) -> str:
        return "https://webapi.legistar.com/v1/spokane"

    @property
    def debug(self) -> bool:
        return os.environ.get("DEBUG", "false").lower() == "true"

    def get_dynamodb_resource(self):
        """Get a DynamoDB resource with proper endpoint configuration."""
        kwargs = {"region_name": self.aws_region}
        if self.dynamodb_endpoint:
            kwargs["endpoint_url"] = self.dynamodb_endpoint
            # For local development, use dummy credentials
            kwargs["aws_access_key_id"] = "local"
            kwargs["aws_secret_access_key"] = "local"
        return boto3.resource("dynamodb", **kwargs)

    def get_dynamodb_table(self, table_name: str):
        """Get a DynamoDB table with proper endpoint configuration."""
        return self.get_dynamodb_resource().Table(table_name)


settings = Settings()
