"""
Chartreuse

Copyright 2018-2020, wiremind.
"""
from setuptools import setup, find_packages

with open("VERSION") as version_file:
    version = version_file.read().strip()


extra_require_test = [
    "mock",
    "pytest",
    "pytest-mock",
]
extra_require_mypy = [
    "mypy",
]
extra_require_dev = ["black", "flake8", "flake8-mutable", "pip-tools>=3.7.0",] + extra_require_mypy + extra_require_test


setup(
    name="chartreuse",
    version=version,
    description="Helper for Alembic / Eslembic migrations within Kubernetes.",
    author="wiremind",
    author_email="dev@wiremind.fr",
    url="https://gitlab.cayzn.com/wiremind/utils/chartreuse.git",
    license="MIT",
    packages=find_packages("src", exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=True,
    python_requires=">=3.6.0",
    install_requires=["alembic==1.*", "eslembic==6.*,>=6.0.2", "psycopg2==2.*", "wiremind-kubernetes>=4.0.1-dev0",],
    extras_require={"dev": extra_require_dev, "mypy": extra_require_mypy, "test": extra_require_test,},
    entry_points={
        "console_scripts": [
            "chartreuse-pre-deployment=chartreuse.predeployment:main",
            "chartreuse-post-deployment=chartreuse.postdeployment:main",
            "chartreuse-post-upgrade=chartreuse.postupgrade:main",
            "chartreuse-post-rollback=chartreuse.postrollback:main",
        ]
    },
)
