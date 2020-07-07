from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='django-async-downloads',
    version='0.1.2',
    author='David Vaughan',
    author_email='david.vaughan@quickrelease.co.uk',
    description='Asynchronous downloads scaffolding for Django projects',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/QuickRelease/django-async-downloads.git',
    packages=find_packages(),
    install_requires=['Django>=2.2.13', 'celery>=4.2.1'],
)
