from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="screenplay-formatter",
    version="1.0.0",
    author="Screenplay Formatter Team",
    description="A comprehensive tool to format text into industry-standard screenplays",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/screenplay-formatter",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=[
        "python-docx>=1.2.0",
        "reportlab>=4.0.0",
        "pydantic>=2.0.0",
        "click>=8.1.0",
    ],
    entry_points={
        "console_scripts": [
            "screenplay-format=screenplay_formatter.cli:main",
        ],
    },
)