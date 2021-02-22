import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="AutoBiller",
    version="0.0.6",
    author="Joseph Yudelson",
    author_email="",
    description="A tool for therapists to turn an icloud calendar of sessions into formal sessions.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JYudelson1/AutoBiller",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'AutoBiller = AutoBiller.__main__:main',
        ],
    },
)
