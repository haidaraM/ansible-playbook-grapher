#!/usr/bin/env bash

set -e

RED='\033[0;31m'
NC='\033[0m'
GREEN='\033[32m'

if [[ "$#" -ne 2 ]]; then
    echo -e "${RED}You must provide the virtualenv directory and the Ansible version to use.${NC}"
    echo -e "${RED}Usage: test_install.sh virtualenv_dir ansible_version. ${NC}"
    exit 1
fi

VIRTUALENV_DIR=$1
ANSIBLE_VERSION=$2

virtualenv --clear ${VIRTUALENV_DIR}

source ${VIRTUALENV_DIR}/bin/activate

pip -V

package=dist/$(ls dist)

echo -e "${GREEN}Installing the packages ${package} and ansible ${ANSIBLE_VERSION} ${NC}"

pip install -q ${package} ansible==${ANSIBLE_VERSION}

${VIRTUALENV_DIR}/bin/ansible-playbook-grapher --version
${VIRTUALENV_DIR}/bin/ansible-playbook-grapher tests/fixtures/example.yml
