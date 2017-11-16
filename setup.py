from setuptools import setup, find_packages
from ansibleplaybookgrapher import __version__, __prog__

try:
    long_description = open('Readme.md').read()
except:
    long_description = None

setup(name=__prog__,
      version=__version__,
      description="A command line tool to create a graph representing your Ansible playbook tasks and roles",
      long_description=long_description,
      url="https://github.com/haidaraM/ansible-playbook-grapher",
      author="HAIDARA Mohamed El Mouctar",
      author_email="elmhaidara@gmail.com",
      license="MIT",
      install_requires=['graphviz', 'colour', 'lxml'],
      packages=find_packages(exclude=['tests']),
      package_data={"ansible-playbook-grapher": ['data/*']},
      include_package_data=True,
      download_url="https://github.com/haidaraM/ansible-playbook-grapher/archive/v" + __version__ + ".tar.gz",
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Environment :: Console',
          'Topic :: Utilities',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 2.7',
      ],
      entry_points={
          'console_scripts': [
              '%s = ansibleplaybookgrapher:main' % __prog__
          ]
      })
