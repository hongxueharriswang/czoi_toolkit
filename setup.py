
from setuptools import setup, find_packages
setup(
    name="czoi",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "sqlalchemy>=1.4",
        "click>=8.0",
        "pyyaml>=5.4",
        "numpy>=1.19",
        "scikit-learn>=0.24",
    ],
    extras_require={
        "neural": ["torch", "transformers"],
        "api": ["fastapi", "uvicorn"],
        "django": ["django>=3.2"],
        "flask": ["flask>=2.0"],
    },
    entry_points={
        "console_scripts": [
            "czoi = czoi.cli.main:cli",
        ],
    },
    author="Harris Wang",
    author_email="harrisw@athabascau.ca",
    description="Python toolkit for Constrained Zoned-Object Architecture",
    license="MIT",
    url="https://github.com/harriswang/czoi",
)
