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
         'Flask-Script==2.0.6',
         'Flask-WTF>=0.14.2',
         'Flask<1.1,>=1.0.2',
         'Flask-Login>=0.2.11',
         'boto3==1.7.83',
         'botocore<1.11.0',
         'contextlib2>=0.4.0',
         'cryptography<2.4,>=2.3',
         'mailchimp3==2.0.11',
         'mandrill>=1.0.57',
         'monotonic>=0.3',
         'notifications-python-client<6.0.0,>=5.0.1',
         'odfpy==1.3.6',
         'python-json-logger==0.1.4',
         'pytz',
         'unicodecsv==0.14.1',
         'Werkzeug==0.14.1',
         'workdays>=1.4',
    ],
)
