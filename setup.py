#!/usr/bin/env python

"""The setup script."""

from setuptools import find_packages, setup

with open("README.md") as readme_file:
    readme = readme_file.read()

with open("requirements.txt") as reqs:
    requirements = [line.strip() for line in reqs.readlines()]

setup_requirements = []

test_requirements = []


setup(
    author="Nick Groszewski",
    author_email="groszewn@gmail.com",
    python_requires=">=3.5",
    entry_points={"console_scripts": ["nks_server=tcp_server.tcp_server:run"]},
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="TCP Server to handle interval searches",
    install_requires=requirements,
    license="MIT license",
    include_package_data=True,
    keywords="tcp_server",
    name="tcp_server",
    packages=find_packages(include=["tcp_server", "tcp_server.*"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/groszewn/tcp_server",
    version="0.1.0",
    zip_safe=False,
)
