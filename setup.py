import setuptools

with open("README.md",  "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pisces",
    version="0.7.0",
    author="Anthony Horton",
    author_email="anthony.horton@drhotdog.net",
    description="Pisces aquarium control system for Raspberry Pi",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AnthonyHorton/pisces",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Licence :: OSI Approved :: BSD 3 Clause",
        "Operating System :: Raspbian",
    ],
)
