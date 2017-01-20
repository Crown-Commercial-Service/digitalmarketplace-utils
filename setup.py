"""
Common utils for Digital Marketplace apps.
"""
import re
import ast
import pip.download
from pip.req import parse_requirements
from setuptools import setup, find_packages


_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('dmutils/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

setup(
    name='digitalmarketplace-utils',
    version=version,
    url='https://github.com/alphagov/digitalmarketplace-utils',
    license='MIT',
    author='GDS Developers',
    description='Common utils for Digital Marketplace apps.',
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'boto==2.38.0',
        'contextlib2==0.4.0',
        'Flask>=0.10',
        'six==1.9.0',
        'pyyaml==3.11',
        'python-json-logger==0.1.4',
        'inflection==0.2.1',
        'Flask-FeatureFlags==0.6',
        'mandrill==1.0.57',
        'monotonic==0.3',
        'pytz==2015.4',
        'Flask-WTF==0.12',
        'Flask-Script==2.0.5',
        'workdays==1.4',
        'unicodecsv==0.14.1',
        'cryptography==1.6'
        'notifications-python-client==4.0.0'
    ]
)
