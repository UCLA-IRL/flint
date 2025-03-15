from setuptools import setup, find_packages

setup(
    name="ndn-compute-util",
    version="0.1",
    packages=find_packages(),  # Automatically find subpackages
    install_requires=[
        "python-ndn==0.5.0",
        "docker==7.1.0",
    ],
)
