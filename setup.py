#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="a2z-agent-top",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[],
    entry_points={
        "console_scripts": [
            "agent-top=a2z_agent_top.cli:main",
            "atop=a2z_agent_top.cli:main",
        ],
    },
)
