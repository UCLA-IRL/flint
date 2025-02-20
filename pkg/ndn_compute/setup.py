from setuptools import setup, find_packages

setup(
    name="ndn-compute",
    version="0.1",
    packages=find_packages(),  # Automatically find subpackages
    install_requires=[
        "python-ndn==0.5.0",
        "nest-asyncio==1.6.0",
        "dill==0.3.9",
    ],
)
