ANSIBLE_VERSION=2.4
VIRTUALENV_DIR=venv
PACKAGE := dist/$(shell ls dist 2> /dev/null)
SRC=$(wildcard ansibleplaybookgrapher/*.py setup.py)

build: $(PACKAGE)

$(PACKAGE): $(SRC)
	@echo "Building the package..."
	@python3 setup.py bdist_wheel

deploy: build
	@twine upload dist/*

setup_virtualenv:
	@./test_install.sh $(VIRTUALENV_DIR) $(ANSIBLE_VERSION)

test_install: build setup_virtualenv

test:
	pytest

clean:
	@echo "Cleaning..."
	@rm -rf ansible_playbook_grapher.egg-info build dist $(VIRTUALENV_DIR) htmlcov .pytest_cache

.PHONY: clean test_install