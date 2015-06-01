#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='bgjobs',
    version='0.1',
    author='Krzysztof Rusek',
    author_email='savix5@gmail.com',
    description='Run and monitor background jobs',
    url='https://github.com/rusek/bgjobs',
    license='The MIT License (MIT)',
    keywords='background jobs, background tasks',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries',
    ],
)
