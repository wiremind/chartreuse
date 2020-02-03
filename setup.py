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
    cmdclass={"test": NoseTestCommand},
    python_requires='>=3.5.0',
    install_requires=[
        "alembic",
        "eslembic>=5.0.1",
        "psycopg2",
        "wiremind-kubernetes>=2.0.0",
    ],
    extras_require={
        'dev': [
            'nose>=1.0',
            'mock',
            'coverage',
            'pip-tools>=3.7.0',
        ]
    },
    entry_points={
        "console_scripts": [
            "chartreuse-pre-deployment=chartreuse.predeployment:main",
            "chartreuse-post-deployment=chartreuse.postdeployment:main",
            "chartreuse-post-rollback=chartreuse.postrollback:main",
        ]
    },
)
