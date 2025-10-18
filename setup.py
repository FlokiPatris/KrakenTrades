# setup.py
from setuptools import find_packages, setup

setup(
    name="trades_src",
    version="0.1.0",
    packages=find_packages("src"),  # find packages under src/
    package_dir={"": "src"},  # maps top-level imports to src/
)
