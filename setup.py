from setuptools import find_packages
from distutils.core import setup


setup(
    name = 'schedpack',
    packages = ['schedpack'],
    version = '0.1.3',
    license = 'MIT',
    description = 'Package for scheduling activities that last some time',
    author = 'borisoid',
    url = 'https://github.com/Borisoid/schedpack',
    keywords = ['schedule', 'lasting', 'cron'],
    install_requires = [
        'croniter==1.0.15',
    ],
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
    ],
)
