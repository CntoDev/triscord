#!/bin/env python3
# -*- coding: utf-8 -*-

"""setuptools-powered setup module."""

import codecs
import os
from setuptools import setup, find_packages

PARENT_DIR = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(PARENT_DIR, 'README.rst'), encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()

setup(
    name='triscord',
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    description='Trello to Discord integration bot',
    long_description=LONG_DESCRIPTION,
    license='BSD 3-Clause License',
    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: System Administrators',

        'Topic :: Communications :: Chat',
        'Topic :: Utilities',

        'License :: OSI Approved :: BSD License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ],
    keywords='trello discord integration',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=[
        'requests>=2.13,<3',
        'arrow==0.10',
    ],
    extras_require={
        'dev': [
            'ipython>=5.3,<6',
        ],
        'test': [
            'pytest>=3.0,<4',
            'coverage>=4.3,<5',
            'pytest-cov>=2.4,<3',
            'pep8>=1.7,<2',
            'pytest-pep8>=1.0,<2',
            'pylint>=1.6,<2',
            'pytest-pylint>=0.7',
            'pytest-mock>=1.5,<2',
        ],
    },
    entry_points={
        'console_scripts': [
            'triscord=triscord:entry_point',
        ],
    },
)

#  vim: set tabstop=4 shiftwidth=4 expandtab autoindent :
