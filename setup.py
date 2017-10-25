from setuptools import setup, find_packages
from ansibleplaybookgrapher import __version__

try:
    long_description = open('README.md').read()
except:
    long_description = None

setup(name="ansible-playbook-grapher",
      version=__version__,
      description="A command line tool to create a graph representing your Ansible playbook tasks and roles",
      url="https://todo",
      author="HAIDARA Mohamed El Mouctar",
      author_email="elmhaidara@gmail.com",
      license="MIT",
      install_requires=['graphviz'],
      packages=find_packages(exclude=['tests']),
      download_url="todo",
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 2.7',
      ],
      entry_points={
          'console_scripts': [
              'ansible-playbook-grapher = ansibleplaybookgrapher:main'
          ]
      })
