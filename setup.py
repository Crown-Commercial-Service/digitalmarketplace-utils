"""
Common utils for Digital Marketplace apps.
"""
import re
import ast
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
         'Flask-FeatureFlags==0.6',
         'Flask-Script==2.0.5',
         'Flask-WTF==0.12',
         'Flask>=0.10',
         'boto==2.38.0',
         'contextlib2==0.4.0',
         'cryptography==1.6',
         'inflection==0.2.1',
         'mandrill==1.0.57',
         'monotonic==0.3',
         'notifications-python-client==4.0.0',
         'python-json-logger==0.1.4',
         'pytz==2015.4',
         'pyyaml==3.11',
         'six==1.9.0',
         'unicodecsv==0.14.1',
         'workdays==1.4'
    ],
    dependency_links=[
        'git+https://github.com/alphagov/notifications-python-client.git@4.0.0#egg=notifications-python-client-4.0.0'
    ],
    extras_require={
        'test': [
            'coverage==3.7.1',
            'freezegun==0.3.4',
            'mock==1.0.1',
            'pep8==1.6.2',
            'pytest-cov==2.2.0',
            'pytest==2.8.7',
            'python-coveralls==2.5.0'
        ]
    }
)
