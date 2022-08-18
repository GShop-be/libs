from setuptools import setup, find_packages

setup(
    name='db_entities',
    python_requires=">=3.10",
    version='0.0.1',
    packages=find_packages(
        where='src'
    ),
    package_dir={"": "src"},
    install_requires=[
        'sqlalchemy==1.4.39',
        'asyncpg==0.26.0',
        'alembic==1.8.1',
    ],
)