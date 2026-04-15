"""Setup configuration for cli-anything-cbeta."""

from setuptools import setup, find_packages

setup(
    name="cli-anything-cbeta",
    version="1.0.0",
    description="CBETA API CLI - 中华电子佛典协会命令行工具",
    author="User",
    packages=find_packages(),
    namespace_packages=["cli_anything"],
    install_requires=[
        "click>=8.0",
        "requests>=2.28",
    ],
    entry_points={
        "console_scripts": [
            "cli-anything-cbeta=cli_anything.cbeta:main",
        ],
    },
    python_requires=">=3.10",
)