from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="geom",
    version="1.0.0",
    author="Pablo Grobas Illobre",
    author_email="pgrobasillobre@gmail.com",
    description="GEOM: A CLI for geometry manipulation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pgrobasillobre/geom",
    packages=find_packages(include=["geom", "geom.*"]),
    entry_points={
        "console_scripts": [
            "geom = geom.__main__:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering",
    ],
    python_requires=">=3.6",
    include_package_data=True,
)
