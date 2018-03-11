============
Installation
============

Python 3.6 or higher is required.

Snakemake 4.4.0 or higher is required.

To clone the repository: :code:`git clone https://github.com/nh13/snakeparse.git`.

To install locally: :code:`python setup.py install`.

The command line utility can be run with :code:`snakeparse`

Conda Recipe
============

See the `conda-recipe <https://github.com/nh13/snakeparse/tree/conda-recipe>`_ branch and the following `pull-request <https://github.com/bioconda/bioconda-recipes/pull/8229>`_ into bioconda.

Testing
=======

To run tests, run :code:`coverage run -m unittest discover -s src`

To obtain test coverage, run :code:`codecov`.
