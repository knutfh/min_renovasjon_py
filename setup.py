import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="min-renovasjon",
    version="0.0.1",
    author="Knut Flage Henriksen",
    author_email="post@flaksen.com",
    description="A package to retrieve waste collections from the Norwegian service Min Renovasjon",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/knutfh/min_renovasjon_py",
    packages=setuptools.find_packages(),
    classifiers=["Programming Language :: Python :: 3",
                 "License :: OSI Approved :: Apache Software License"],
    python_requires=">=3.7",
)
