"""Setup configuration for PyeChat."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pyechat",
    version="0.1.0",
    author="Colby",
    description="A modern IRC client built with PyQt5",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ComputerTech312/pyechat",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Communications :: Chat :: Internet Relay Chat",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PyQt5>=5.15.0",
    ],
    entry_points={
        "console_scripts": [
            "pyechat=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["assets/*", "data/*.example.json"],
    },
)
