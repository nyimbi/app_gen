from setuptools import find_packages, setup

# Read the dependencies specified in 'requirements.txt'
with open("requirements.txt") as f:
    required = [line.strip() for line in f if not line.startswith("#")]

setup(
    name="my_project",
    version="0.1.0",  # You can update this with each release
    description="A flask-appbuilder mixin to track create,update, delete and read accesses to rows in a table",
    author="Your Name Here <your_email@example.com>",
    packages=find_packages(),
    install_requires=required,
    entry_points={
        "console_scripts": [
            # Entry point for any command-line tools you want installed
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",  # Update this according to your license choice.
        "Operating System :: MacOS | Windows | Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
