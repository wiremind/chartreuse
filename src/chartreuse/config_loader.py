"""
Simple configuration loader for multi-database support.
"""

import logging
from typing import Dict, List

import yaml

logger = logging.getLogger(__name__)


def build_database_url(db_config: Dict) -> str:
    """
    Build database URL from individual components.

    Builds URL from: dialect, user, password, host, port, database
    """
    # Build URL from components
    required_components = ["dialect", "user", "password", "host", "port", "database"]
    missing_components = [
        comp
        for comp in required_components
        if comp not in db_config or not db_config[comp]
    ]

    if missing_components:
        raise ValueError(f"Missing required components: {missing_components}")

    dialect = db_config["dialect"]
    user = db_config["user"]
    password = db_config["password"]
    host = db_config["host"]
    port = db_config["port"]
    database = db_config["database"]

    return f"{dialect}://{user}:{password}@{host}:{port}/{database}"


def load_multi_database_config(config_path: str) -> List[Dict]:
    """
    Load multi-database configuration from YAML file.

    Expected format:
    databases:
      main:
        alembic_directory_path: /app/alembic/main
        alembic_config_file_path: alembic.ini
        dialect: postgresql
        user: myuser
        password: mypassword
        host: localhost
        port: 5432
        database: mydb
        allow_migration_for_empty_database: true
        additional_parameters: ""
    """
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        if "databases" not in config:
            raise ValueError("Configuration must contain 'databases' key")

        databases_dict = config["databases"]

        if not isinstance(databases_dict, dict):
            raise ValueError(
                "'databases' must be a dictionary with database names as keys"
            )

        # Convert dictionary to list format for internal processing
        databases = []
        for db_name, db_config in databases_dict.items():
            # Add the database name to the config
            db_config["name"] = db_name

            # Build URL from components
            db_config["url"] = build_database_url(db_config)

            databases.append(db_config)

        return databases

    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in configuration file: {e}")
