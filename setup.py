import sys

from setuptools import setup, find_packages

from ansibleplaybookgrapher import __version__, __prog__

with open('Readme.md') as f:
    long_description = f.read()

# add `pytest-runner` distutils plugin for test;
# see https://pypi.python.org/pypi/pytest-runner
setup_requires = []
if {'pytest', 'test', 'ptr'}.intersection(sys.argv[1:]):
    setup_requires.append('pytest-runner')

setup(name=__prog__,
      version=__version__,
      description="A command line tool to create a graph representing your Ansible playbook tasks and roles",
      long_description=long_description,
      long_description_content_type='text/markdown',
      url="https://github.com/haidaraM/ansible-playbook-grapher",
      author="HAIDARA Mohamed El Mouctar",
      author_email="elmhaidara@gmail.com",
      license="MIT",
      install_requires=['graphviz==0.10.1', 'colour==0.1.5', 'lxml==4.2.5', 'ansible>=2.4.0'],
      tests_require=['pytest', 'pytest-cov', 'pyquery'],
      setup_requires=setup_requires,
      packages=find_packages(exclude=['tests']),
      package_data={"ansible-playbook-grapher": ['data/*']},
      include_package_data=True,
      download_url="https://github.com/haidaraM/ansible-playbook-grapher/archive/v" + __version__ + ".tar.gz",
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: MIT License',
          'Environment :: Console',
          'Topic :: Utilities',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 2.7',
      ],
      entry_points={
          'console_scripts': [
              '%s = ansibleplaybookgrapher.cli:main' % __prog__
          ]
      })
