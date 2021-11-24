"""
Chartreuse
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
extra_require_dev = (
    [
        "black",
        "flake8",
        "flake8-mutable",
        "pip-tools",
    ]
    + extra_require_mypy
    + extra_require_test
)


setup(
    name="chartreuse",
    version=version,
    description="Helper for Alembic migrations within Kubernetes.",
    author="wiremind",
    author_email="dev@wiremind.io",
    url="https://github.com/wiremind/chartreuse",
    license="LGPLv3+",
    packages=find_packages("src", exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=True,
    python_requires=">=3.7.0",
    install_requires=[
        "alembic==1.*",
        "psycopg2==2.*",
        "wiremind-kubernetes==6.*,>=6.3.5",
    ],
    extras_require={
        "dev": extra_require_dev,
        "mypy": extra_require_mypy,
        "test": extra_require_test,
    },
    entry_points={"console_scripts": ["chartreuse-upgrade=chartreuse.chartreuse_upgrade:main"]},
)
