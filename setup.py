from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='django-async-downloads',
    version='0.2.2',
    author='David Vaughan',
    author_email='david.vaughan@quickrelease.co.uk',
    maintainer="Quick Release (Automotive) Ltd.",
    description='Asynchronous downloads scaffolding for Django projects',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/QuickRelease/django-async-downloads.git',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: Django :: 2.0",
        "Framework :: Django :: 2.1",
        "Framework :: Django :: 2.2",
        "Framework :: Django :: 3.0",
        "Framework :: Django :: 3.1",
        "Framework :: Django :: 3.2",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
    ],
    keywords="django download asynchronous async celery",
    packages=["async_downloads"],
    include_package_data=True,
    install_requires=['Django>=2.0', 'celery>=4.2.1', 'pathvalidate>=2.3.0'],
    license="MIT",
)
