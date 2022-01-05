#!/usr/bin/env python3

import os
from setuptools import setup, find_packages


VERSION = '0.1.0'

reqs_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')

with open(reqs_path, 'r') as req_file:
    dependencies = req_file.readlines()

setup(
    name='git_lp_revert_mp',
    version=VERSION,
    packages=find_packages(),
    install_requires=dependencies,
    license='GPLv3',
    entry_points={
        'console_scripts': ['git-lp-revert-mp=git_lp_revert_mp:revert_mp'],
    }
)
