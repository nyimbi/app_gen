
from setuptools import setup, find_namespace_packages

setup(
    name="WebScraper",
    version="1.0",
    description="Advanced web scraping library",
    author="",
    packages=find_namespace_packages(include=["webscraper.*"]),
    package_dir={"": "src"},
    install_requires=[

        "aiohttp>=3.8.0",

        "beautifulsoup4>=4.9.0",

        "readability-lxml>=0.8.1",

        "redis>=4.0.0",

        "nltk>=3.6.0",

        "prometheus_client>=0.12.0",

        "langdetect>=1.0.9",

        "pyyaml>=5.4.0",

    ],
    python_requires=">=3.7",
    extras_require={
        "dev": [
            "pytest",
            "pytest-cov",
            "black",
            "isort",
            "mypy",
            "sphinx",
        ]
    },
)
