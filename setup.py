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
    package_data={'dmutils': ['py.typed']},
    include_package_data=True,
    install_requires=[
         'Flask-WTF>=0.14.2',
         'Flask~=1.0',
         'Flask-gzip>=0.2',
         'Flask-Login>=0.2.11',
         'Flask-Session>=0.3.2',
         'boto3<2,>=1.7.83',
         'contextlib2>=0.4.0',
         'cryptography>=3.2',
         'gds-metrics>=0.2.0,<1',
         'govuk-country-register>=0.3.0',
         'mailchimp3==3.0.15',
         'requests>=2.22.0,<3',
         'redis>=3.5.2',
         'fleep<1.1,>=1.0.1',
         'notifications-python-client>=5.0.1,<7.0.0',
         'odfpy>=1.3.6',
         'python-json-logger>=0.1.11,<3.0.0',
         'pytz',
         'unicodecsv>=0.14.1',
         'workdays>=1.4',
    ],
    python_requires="~=3.8",
)
