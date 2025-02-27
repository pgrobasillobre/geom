from setuptools import setup, find_packages

setup(
    name="geom",
    version="1.0.0",
    author="Pablo Grobas Illobre",
    description="GEOM: A CLI for geometry manipulation",
    packages=find_packages(),
    install_requires=[
        "ase==3.22.1",
        "gmsh==4.11.1",
        "numpy==1.24.3",
        "pytest==8.3.4",  # Remove if not needed for installation
    ],
    entry_points={
        "console_scripts": [
            "geom = geom.__main__:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)

