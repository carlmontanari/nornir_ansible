#!/usr/bin/env python
"""nornir ansible inventory plugin"""
import setuptools

__author__ = "Carl Montanari"

with open("README.md", "r") as f:
    README = f.read()

setuptools.setup(
    name="nornir_ansible",
    version="2020.04.11",
    author=__author__,
    author_email="carl.r.montanari@gmail.com",
    description="",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/carlmontanari/nornir_ansible",
    packages=setuptools.find_packages(),
    install_requires=["mypy_extensions>=0.4.1", "ruamel.yaml>=0.16.10", "nornir>=2.4.0"],
    extras_require={},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    python_requires=">=3.6",
)
