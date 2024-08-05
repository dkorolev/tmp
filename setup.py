from setuptools import setup, find_packages


def get_reqs(file="requirements.txt"):
    with open(file) as f:
        return [s.rstrip("\n") for s in f.readlines()]

setup(
    name="pls",
    version="0.1",
    packages=find_packages(),
    install_requires=get_reqs(),
    author="Dima Korolev",
    author_email="dima@current.ai",
    description="C/C++ Build Tool",
    include_package_data=True,
    entry_points={"console_scripts": ["pls=pls.functions:main"]},
)
