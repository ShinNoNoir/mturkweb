#!/usr/bin/env python
import os
import sys

if sys.version < '2.6':
    print 'Python >= 2.6 required'
    sys.exit(1)

from setuptools import setup

long_description = '''
A simple Amazon Mechanical Turk (AMT) library for retrieving information 
about batches that were created in the AMT web interface.'''.strip()

setup(
    name = 'mturkweb',
    version='0.1.2',
    author = 'Raynor Vliegendhart',
    author_email = 'ShinNoNoir@gmail.com',
    url = 'https://github.com/ShinNoNoir/mturkweb',
    
    packages=['mturkweb'],
    
    description = "Library for Mechanical Turk's web interface",
    long_description = long_description,
    platforms = 'Any',
    license = 'MIT (see: LICENSE.txt)',
    keywords = 'Amazon, Mechanical Turk, MTurk',
    
    install_requires = [
        'mechanize==0.2.5',
        'beautifulsoup4==4.3.2'
    ],
)

