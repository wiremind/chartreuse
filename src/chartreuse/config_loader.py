"""
Configuration loader for multi-database support using Pydantic models.
"""

import logging

import yaml
from pydantic import BaseModel, Field, computed_field, field_validator

logger = logging.getLogger(__name__)


class DatabaseConfig(BaseModel):
    """Configuration for a single database within a multi-database setup."""

    # Database connection components
    dialect: str = Field(..., description="Database dialect (e.g., postgresql)")
    user: str = Field(..., description="Database user")
    password: str = Field(..., description="Database password")
    host: str = Field(..., description="Database host")
    port: int = Field(..., description="Database port", gt=0, le=65535)
    database: str = Field(..., description="Database name")

    # Alembic configuration
    alembic_directory_path: str = Field(..., description="Path to Alembic directory")
    alembic_config_file_path: str = Field(default="alembic.ini", description="Path to Alembic config file")

    # Optional migration settings
    allow_migration_for_empty_database: bool = Field(default=True, description="Allow migrations on empty database")
    additional_parameters: str = Field(default="", description="Additional Alembic parameters")

    @computed_field
    @property
    def url(self) -> str:
        """Build database URL from components."""
        return f"{self.dialect}://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @field_validator("dialect")
    @classmethod
    def validate_dialect(cls, v: str) -> str:
        """Validate database dialect."""
        supported_dialects = ["postgresql", "mysql", "sqlite", "oracle", "mssql", "clickhouse"]
        if v.lower() not in supported_dialects:
            logger.warning("Dialect '%s' might not be supported. Supported dialects: %s", v, supported_dialects)
        return v

    @field_validator("additional_parameters")
    @classmethod
    def validate_additional_parameters(cls, v: str) -> str:
        """Ensure additional_parameters is a string."""
        return v or ""


class MultiDatabaseConfig(BaseModel):
    """Multi-database configuration - the only supported configuration format."""

    databases: dict[str, DatabaseConfig] = Field(..., description="Dictionary of database configurations")

    @field_validator("databases")
    @classmethod
    def validate_databases_not_empty(cls, v: dict[str, DatabaseConfig]) -> dict[str, DatabaseConfig]:
        """Ensure at least one database is configured."""
        if not v:
            raise ValueError("At least one database must be configured")
        return v


def load_multi_database_config(config_path: str) -> dict[str, DatabaseConfig]:
    """
    Load multi-database configuration from YAML file using Pydantic validation.

    This is the only supported configuration format. Single database setups should
    be configured as a multi-database config with one entry.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Dictionary of database configurations keyed by database name

    Raises:
        FileNotFoundError: If configuration file is not found
        ValueError: If configuration is invalid

    Expected YAML format:
    ```yaml
    databases:
      main:  # Database name/identifier
        dialect: postgresql
        user: app_user
        password: app_password
        host: postgres-main
        port: 5432
        database: app_main
        alembic_directory_path: /app/alembic/main
        alembic_config_file_path: alembic.ini
        allow_migration_for_empty_database: true
        additional_parameters: ""

      # For single database setups, just include one database:
      # analytics:
      #   dialect: postgresql
      #   user: analytics_user
      #   password: analytics_password
      #   host: postgres-analytics
      #   port: 5432
      #   database: analytics
      #   alembic_directory_path: /app/alembic/analytics
      #   alembic_config_file_path: alembic.ini
      #   allow_migration_for_empty_database: false
      #   additional_parameters: ""
    ```
    """
    try:
        with open(config_path) as f:
            raw_config = yaml.safe_load(f)

        # Validate the configuration using Pydantic
        config = MultiDatabaseConfig(**raw_config)

        logger.info(
            "Loaded configuration for %d database(s): %s", len(config.databases), ", ".join(config.databases.keys())
        )

        return config.databases

    except FileNotFoundError as err:
        raise FileNotFoundError(f"Configuration file not found: {config_path}") from err
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in configuration file: {e}") from e
    except Exception as e:
        raise ValueError(f"Invalid configuration: {e}") from e
