from setuptools import setup
import os

here = os.path.abspath(os.path.dirname(__file__))

setup(
    name="BIDS2NDA",

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # http://packaging.python.org/en/latest/tutorial.html#version
    version='0.2.0',

    description="Command line tool generating NDA compatible description from a Brain Imaging Data Structure "
                "compatible dataset.",
    long_description="Command line tool generating NDA compatible description from a Brain Imaging Data Structure "
                     "compatible dataset.",

    # The project URL.
    url='https://github.com/INCF/BIDS2NDA',

    # Choose your license
    license='BSD',

    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: BSD License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
    ],

    # What does your project relate to?
    keywords='BIDS NDA NDAR NIMH',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages.
    packages=["bids2nda",
              "bids2nda.tests",
              ],

    # List run-time dependencies here.  These will be installed by pip when your
    # project is installed.
    install_requires = ["future",
                        "pandas",
                        'nibabel'],

    include_package_data=True,

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'bids2nda=bids2nda.main:main',
        ],
    },
)
