"""
Setup script for RAG Chatbot Python API Client
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ragchatbot-api-client",
    version="1.0.0",
    author="RAG Chatbot Team",
    author_email="support@ragchatbot.com",
    description="Python client library for RAG Chatbot PWA API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/ragchatbot-api-client",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
        "dataclasses>=0.6;python_version<'3.7'",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        "async": [
            "aiohttp>=3.7.0",
            "asyncio>=3.4.3",
        ],
    },
    entry_points={
        "console_scripts": [
            "ragchatbot-cli=ragchatbot_client.cli:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/your-org/ragchatbot-api-client/issues",
        "Source": "https://github.com/your-org/ragchatbot-api-client",
        "Documentation": "https://docs.ragchatbot.com/api-client",
    },
)
