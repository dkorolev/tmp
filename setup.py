from setuptools import setup, find_packages


def get_reqs(file="requirements.txt"):
    with open(file) as f:
        return [s.rstrip("\n") for s in f.readlines()]

def get_version(file='./pls/static/version'):
    with open(file, 'r') as reader:
        version = reader.read()
        return version


setup(
    name="pls",
    version=get_version(),
    packages=find_packages(),
    install_requires=get_reqs(),
    author="Dima Korolev",
    author_email="dima@current.ai",
    description="C/C++ Build Tool",
    include_package_data=True,
    entry_points={"console_scripts": ["pls=pls.cmd:main"]},
)
