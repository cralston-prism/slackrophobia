#!/usr/bin/env python

from distutils.core import setup

setup(
    name='slackrophobia',
    version='1.0',
    description='acronym game',
    author='czeano',
    url='https://github.com/czeano/slackrophobia',
    py_modules=['slackrophobia.py', ],
    requires=['slackclient', ],
)
