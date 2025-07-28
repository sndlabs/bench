from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="snd-bench",
    version="0.1.0",
    author="SND Bench Team",
    author_email="",
    description="A comprehensive benchmarking framework for language models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/snd-bench",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "snd-bench=snd_bench.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "snd_bench": ["configs/*.yaml", "configs/*.json"],
    },
)