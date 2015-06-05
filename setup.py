"""
Common utils for Digital Marketplace apps.
"""
import re
import ast
import pip.download
import itertools
from pip.req import parse_requirements
from setuptools import setup


_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('dmutils/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

requirements = list(parse_requirements('requirements.txt', session=pip.download.PipSession()))

install_requires = [str(r.req) for r in requirements]

setup(
    name='digitalmarketplace-utils',
    version=version,
    url='https://github.com/alphagov/digitalmarketplace-utils',
    license='MIT',
    author='GDS Developers',
    description='Common utils for Digital Marketplace apps.',
    long_description=__doc__,
    packages=['dmutils'],
    include_package_data=True,
    install_requires=install_requires
)
