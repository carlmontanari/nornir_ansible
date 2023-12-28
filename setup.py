#!/usr/bin/env python
"""nornir ansible inventory plugin"""
import setuptools

__author__ = "Carl Montanari"

with open("README.md", "r", encoding="utf-8") as f:
    README = f.read()

setuptools.setup(
    name="nornir_ansible",
    version="2022.07.30",
    author=__author__,
    author_email="carl.r.montanari@gmail.com",
    description="",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/carlmontanari/nornir_ansible",
    packages=setuptools.find_packages(),
    install_requires=[
        "ruamel.yaml>=0.16.10,<1.0.0",
        "nornir>=3.4.0,<4.0.0",
    ],
    extras_require={},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    entry_points="""
    [nornir.plugins.inventory]
    AnsibleInventory=nornir_ansible.plugins.inventory:AnsibleInventory
    """,
)
