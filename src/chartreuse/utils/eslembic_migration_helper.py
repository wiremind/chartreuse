import re
from subprocess import SubprocessError

from wiremind_kubernetes.utils import run_command

ESLEMBIC_DIRECTORY_PATH = "/app/eslembic"


class EslembicMigrationHelper(object):
    def __init__(self, elasticsearch_url: str, configure: bool = True):
        if not elasticsearch_url:
            raise EnvironmentError("elasticsearch_url not set, not upgrading elasticsearch.")

        self.elasticsearch_url = elasticsearch_url

        if configure:
            self._configure()
        self.is_migration_needed = self.check_migration_needed()

    def _configure(self):
        print("Eslembic: configuring for %s" % self.elasticsearch_url)
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
        print(eslembic_current)
        if head_re.search(eslembic_current):
            print("Elasticsearch does not need schema upgrade.")
            return False
        print("Elasticsearch schema can be upgraded.")
        return True

    def upgrade_db(self):
        print("Upgrading Elasticsearch...")
        run_command("eslembic upgrade head", cwd=ESLEMBIC_DIRECTORY_PATH)
        print("Done upgrading Elasticsearch.")

    def migrate_db(self):
        print("Migrating Elasticsearch...")
        run_command("eslembic migrate", cwd=ESLEMBIC_DIRECTORY_PATH)
        print("Done migrating Elasticsearch.")

    def clean_index(self):
        print("Cleaning Elasticsearch...")
        run_command("eslembic clean", cwd=ESLEMBIC_DIRECTORY_PATH)
        print("Done cleaning Elasticsearch.")
