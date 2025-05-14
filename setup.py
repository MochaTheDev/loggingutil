from setuptools import setup, find_packages

setup(
    name="loggingutil",
    version="1.2.2",
    packages=find_packages(),
    install_requires=[],
    author="Mocha",
    author_email="ohplot@gmail.com",
    description="Advanced logging utility with rotation, JSON/text output, and HTTP logging.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/mochathehuman/loggingutil",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)