from setuptools import find_packages, setup

setup(
    name="proxy-client",
    version="0.0.1",
    packages=find_packages(),
    install_requires=[],
    extras_require={
        "dev": ["requests"],
    },
)
