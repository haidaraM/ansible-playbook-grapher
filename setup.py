import sys

from setuptools import setup, find_packages

from ansibleplaybookgrapher import __version__, __prog__


def read_requirements(path):
    """
    Read requirements file
    :param path:
    :type path:
    :return:
    :rtype:
    """
    requirements = []
    with open(path) as f_r:
        for l in f_r:
            requirements.append(l.strip())
    return requirements


install_requires = read_requirements('requirements.txt')
test_require = read_requirements('tests/requirements_tests.txt')[1:]

with open('README.md') as f:
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
      install_requires=install_requires,
      tests_require=test_require,
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
