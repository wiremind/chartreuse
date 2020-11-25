import logging
import re
from subprocess import SubprocessError

from wiremind_kubernetes.utils import run_command


logger = logging.getLogger(__name__)


ESLEMBIC_DIRECTORY_PATH = "/app/eslembic"


class EslembicMigrationHelper:
    def __init__(self, elasticsearch_url: str, configure: bool = True):
        if not elasticsearch_url:
            raise OSError("elasticsearch_url not set, not upgrading elasticsearch.")

        self.elasticsearch_url = elasticsearch_url

        if configure:
            self._configure()
        self.is_migration_needed = self.check_migration_needed()

    def _configure(self):
        logger.info("Eslembic: configuring for %s" % self.elasticsearch_url)
        cleaned_url = self.elasticsearch_url.replace("/", r"\/")
        run_command(
            f"sed -i -e 's/elasticsearch_urls.*=.*/elasticsearch_urls={cleaned_url}/' eslembic.ini",
            cwd=ESLEMBIC_DIRECTORY_PATH,
        )

    def _get_eslembic_current(self):
        eslembic_current, stderr, returncode = run_command(
            "eslembic current", return_result=True, cwd=ESLEMBIC_DIRECTORY_PATH
        )
        if returncode != 0:
            raise SubprocessError(f"eslembic current failed: {eslembic_current}, {stderr}")
        return eslembic_current

    def check_migration_needed(self) -> bool:
        head_re = re.compile(r"\(head\)", re.MULTILINE)
        eslembic_current = self._get_eslembic_current()
        logger.info(eslembic_current)
        if head_re.search(eslembic_current):
            logger.info("Elasticsearch does not need schema upgrade.")
            return False
        logger.info("Elasticsearch schema can be upgraded.")
        return True

    def upgrade_db(self):
        logger.info("Upgrading Elasticsearch...")
        run_command("eslembic upgrade head", cwd=ESLEMBIC_DIRECTORY_PATH)
        logger.info("Done upgrading Elasticsearch.")

    def migrate_db(self):
        logger.info("Migrating Elasticsearch...")
        run_command("eslembic migrate", cwd=ESLEMBIC_DIRECTORY_PATH)
        logger.info("Done migrating Elasticsearch.")

    def clean_index(self):
        logger.info("Cleaning Elasticsearch...")
        run_command("eslembic clean", cwd=ESLEMBIC_DIRECTORY_PATH)
        logger.info("Done cleaning Elasticsearch.")
