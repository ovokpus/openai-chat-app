from setuptools import setup, find_packages

setup(
    name="aimakerspace",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "openai>=1.77.0",
        "numpy>=2.3.1",
        "pypdf>=5.7.0",
        "python-docx>=1.2.0",
        "openpyxl>=3.1",
        "xlrd>=2.0.2",
        "pandas>=2.3.0",
        "python-pptx>=1.0.2"
    ],
    python_requires=">=3.8",
) 