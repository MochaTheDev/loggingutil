from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="loggingutil",
    version="2.0.1",
    author="Mocha",
    author_email="ohplot@gmail.com",
    description=("A powerful logging utility that surpasses the standard library"),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mochathehuman/loggingutil",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Logging",
        "Framework :: AsyncIO",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Information Technology",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.8",
    install_requires=[
        "aiohttp>=3.8.0",
        "pyyaml>=5.1",
        "click>=8.0.0",
    ],
    extras_require={
        "aws": ["boto3>=1.26.0"],
        "elastic": ["elasticsearch>=7.0.0"],
        "metrics": ["prometheus_client>=0.16.0"],
        "structlog": ["structlog>=22.1.0"],
        "all": [
            "boto3>=1.26.0",
            "elasticsearch>=7.0.0",
            "prometheus_client>=0.16.0",
            "structlog>=22.1.0",
            "rich>=12.0.0",  # For enhanced CLI output
            "tabulate>=0.8.0",  # For table formatting
        ],
    },
    entry_points={
        "console_scripts": [
            "loggingutil=loggingutil.cli:main",
        ],
    },
    project_urls={
        "Bug Tracker": "https://github.com/mochathehuman/loggingutil/issues",
        "Source": "https://github.com/mochathehuman/loggingutil",
        "Documentation": (
            "https://mochathehuman.github.io/loggingutil/"
        ),
    },
    keywords=[
        "logging",
        "logs",
        "structured-logging",
        "async-logging",
        "log-rotation",
        "monitoring",
        "observability",
        "cloudwatch",
        "elasticsearch",
        "prometheus",
    ],
)
