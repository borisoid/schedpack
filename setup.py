from pathlib import (
    Path,
)

from setuptools import (
    setup,
)


README = Path("README.md").read_text()


setup(
    name="schedpack",

    packages=["schedpack"],
    version="1.1.1",

    description="Package for scheduling activities that last some time",
    long_description=README,
    long_description_content_type="text/markdown",
    keywords=["schedule", "lasting", "span", "cron"],

    license="MIT",
    author="borisoid",
    url="https://github.com/borisoid/schedpack",

    install_requires=[
        "croniter==1.0.15",
    ],

    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
    ],
)
