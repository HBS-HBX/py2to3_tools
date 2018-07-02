#!/usr/bin/env python

from setuptools import find_packages
from setuptools import setup

setup(
    name='Py2to3 Tools',
    version='1.0',
    description='Python tools to help you migrate from py2 to py3',
    author='HBX Software Team',
    author_email='hbxdev@myhbx.org',
    url='https://github.com/HBS-HBX/py2to3_tools/',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
    ],
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Programming Language :: Python2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Bug Tracking',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Code Generators',
    ],
    keywords=['py26', 'py27', 'python', 'migration'],
)
