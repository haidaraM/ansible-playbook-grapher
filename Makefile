ANSIBLE_VERSION=2.4
VIRTUALENV_DIR=venv
PACKAGE := dist/$(shell ls dist 2> /dev/null)
SRC=$(wildcard ansibleplaybookgrapher/*.py setup.py ansibleplaybookgrapher/data/*)

build: $(PACKAGE)

$(PACKAGE): $(SRC)
	@echo "Building the package..."
	@python3 setup.py bdist_wheel

# Deploy to Pypi Live environment
deploy: clean build
	@echo "Deploying to Pypi Live environment..."
	@twine upload dist/*

# Deploy to Pypi test environment
deploy_test: clean build
	@echo "Deploying to Pypi Test environment..."
	@twine upload --repository-url https://test.pypi.org/legacy/ dist/*

setup_virtualenv:
	@./test_install.sh $(VIRTUALENV_DIR) $(ANSIBLE_VERSION)

test_install: build setup_virtualenv

test:
	pytest

clean:
	@echo "Cleaning..."
	@rm -rf ansible_playbook_grapher.egg-info build dist $(VIRTUALENV_DIR) htmlcov .pytest_cache .eggs

.PHONY: clean test_install