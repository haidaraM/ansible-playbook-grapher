#!/bin/bash

source ./venv/bin/activate
make build
pip install --force dist/*.whl
#ansible-playbook-grapher "${1:-tests/fixtures/playbooks/manage-servers.yml}"
