#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='dice_roller',
    version=0.1,
    description='A dice roller for processing RPG style dice expressions.',
    author='PKnull',
    author_email='louis.grenzebach@gmail.com',
    url='https://github.com/pknull/rpg-dice',
    packages=[
        'dice_roller',
    ],
    install_requires=[
        'sympy',
        'pyparsing'
    ],
    package_dir={'rpg-dice': 'dice_roller'},
    include_package_data=True,
    license='MIT',
    zip_safe=False,
    keywords='rpg dice'
)
