from setuptools import setup, find_packages

setup(
    name='grpc_entities',
    python_requires=">=3.10",
    version='0.0.1',
    packages=find_packages(
        where='src'
    ),
    package_dir={"": "src"},
    install_requires=[
        'grpcio==1.47.0',
        'grpcio-tools==1.47.0',
    ],
)