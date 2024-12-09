# Copyright (C) 2023 Mohamed El Mouctar HAIDARA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sys
from pathlib import Path

from setuptools import find_packages, setup

from ansibleplaybookgrapher import __prog__, __version__


def read_requirements(path: str):
    """Read requirements file
    :param path:
    :type path:
    :return:
    :rtype:
    """
    requirements = []
    with Path(path).open() as f_r:
        for line in f_r:
            requirements.append(line.strip())
    return requirements


install_requires = read_requirements("requirements.txt")
test_require = read_requirements("tests/requirements_tests.txt")[1:]

with Path("README.md").open() as f:
    long_description = f.read()

# add `pytest-runner` distutils plugin for test;
# see https://pypi.python.org/pypi/pytest-runner
setup_requires = []
if {"pytest", "test", "ptr"}.intersection(sys.argv[1:]):
    setup_requires.append("pytest-runner")

setup(
    name=__prog__,
    version=__version__,
    description="A command line tool to create a graph representing your Ansible playbook tasks and roles.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/haidaraM/ansible-playbook-grapher",
    author="HAIDARA Mohamed El Mouctar",
    author_email="elmhaidara@gmail.com",
    license="MIT",
    install_requires=install_requires,
    tests_require=test_require,
    setup_requires=setup_requires,
    packages=find_packages(exclude=["tests"]),
    package_data={"ansible-playbook-grapher": ["data/*"]},
    include_package_data=True,
    download_url="https://github.com/haidaraM/ansible-playbook-grapher/archive/v"
    + __version__
    + ".tar.gz",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Environment :: Console",
        "Topic :: Utilities",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    entry_points={"console_scripts": [f"{__prog__} = ansibleplaybookgrapher.cli:main"]},
)
