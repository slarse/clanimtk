# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

test_requirements = [
    'pytest>=3.1.1', 'pytest-cov>=2.5.1', 'codecov', 'asynctest'
]
required = []

setup(
    name='clanimtk',
    version='0.1.0',
    description='Command line animations made easy!',
    long_description=readme,
    author='Simon Larsén',
    author_email='slarse@kth.se',
    url='https://github.com/slarse/clanimtk',
    download_url='https://github.com/slarse/clanimtk/archive/v0.1.0.tar.gz',
    license=license,
    packages=find_packages(exclude=('tests', 'docs')),
    tests_require=test_requirements,
    install_requires=required,
    include_package_data=True,
    zip_safe=False)
