from setuptools import setup
import sys
if sys.version_info < (3,6):
        sys.exit('Sorry, Python < 3.6 is not supported')

# Get the package version
exec(open('src/snakeparse/version.py').read())
setup(
    name = "snakeparse",
    author = "Nils Homer",
    author_email = "nilshomer@gmail.com",
    version = __version__,
    description = "Making SnakeMake workflows into fully-fledged command line tools since 1999.",
    url = "https://github.com/nh13/snakeparse",
    license = "MIT",
    packages = ['snakeparse'],
    package_dir = {'snakeparse':'src/snakeparse'}, 
    package_data = {},
    install_requires = ['pyhocon>=0.3.38', 'pyyaml>=3.12', 'snakemake>=4.4.0'],
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
    entry_points = {
        'console_scripts': [
            'snakeparse=snakeparse.__main__:main'
        ]
    },
    zip_safe = False,
)
