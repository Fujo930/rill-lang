from setuptools import setup, find_packages

setup(
    name="rill-lang",
    version="0.1.0",
    description="A minimal, expression-oriented programming language",
    author="Rill Team",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "rill=rill.repl:main",
        ],
    },
    python_requires=">=3.10",
)
