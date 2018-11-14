"""
alembic-kubernetes-migrator

Copyright 2018, wiremind.
"""
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

with open('VERSION') as version_file:
    version = version_file.read().strip()

class NoseTestCommand(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # Run nose ensuring that argv simulates running nosetests directly
        import nose

        nose.run_exit(argv=["nosetests"])


setup(
    name="chartreuse",
    version=version,
    description="Helper for Alembic migrations within Kubernetes.",
    author="wiremind",
    author_email="dev@wiremind.fr",
    url="https://gitlab.cayzn.com/wiremind/utils/chartreuse.git",
    license="MIT",
    packages=find_packages("src", exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=True,
    tests_require=["nose>=1.0", "mock"],
    cmdclass={"test": NoseTestCommand},
    install_requires=["wiremind-kubernetes>=0.0.3", "alembic", "requests", "future", "psycopg2"],
    entry_points={
        "console_scripts": [
            "chartreuse-pre-deployment=chartreuse.predeployment:main",
            "chartreuse-post-deployment=chartreuse.postdeployment:main",
        ]
    },
)
