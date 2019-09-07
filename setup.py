try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import re

def get_long_description():
    with open("README.md", "r") as fh:
        readme = fh.read()
    match = re.search(r'([\w\W]+)(- \[Copinicoos\]\(#copinicoos\)[\w\W]+)(## Install[\w\W]+)(##\sDevelopment)', readme)
    long_description = match.group(1) + match.group(3)
    return long_description

setup(
    name="copinicoos",
    version="0.0.1.3",
    packages=["copinicoos"],
    description="Copernicus Download Manager",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Sherry aka potatowagon",
    author_email="e0007652@u.nus.edu",
    url="https://github.com/potatowagon/copinicoos",
    keywords=["copinicoos", "copernicus", "downloader", "radar", "ESA", "EU", "satellite", "sentinel", "sar", "download", "manager"],
    install_requires=["colorama>=0.3.4", "cryptography"],
    extras_require={
        "dev": [
            "codecov>=2.0.15",
            "colorama>=0.3.4",
            "tox>=3.9.0",
            "tox-travis>=0.12",
            "pytest>=4.6.2",
            "pytest-cov>=2.7.1",
            "Pillow>=5.0.0",
            "psutil"
        ]
    },
    python_requires=">=3.7",
)