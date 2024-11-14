from setuptools import setup

setup(
    name='appgen',
    version='0.1.0',
    py_modules=['gen'],
    install_requires=[
        'Click',
        'sqlalchemy'
    ],
    entry_points={
        'console_scripts': [
            'yourscript = yourscript:cli',
        ],
    },
)