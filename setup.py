from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='helmut',
      version=version,
      description="Reconciliation API Server",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='recon google refine api server',
      author='Friedrich Lindenberg',
      author_email='friedrich.lindenberg@okfn.org',
      url='http://okfn.org',
      license='AGPLv3',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
