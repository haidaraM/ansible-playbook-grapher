ANSIBLE_VERSION=2.10.7
VIRTUALENV_DIR=venv-test-install
PACKAGE := dist/$(shell ls dist 2> /dev/null)
SRC=$(wildcard ansibleplaybookgrapher/*.py setup.py ansibleplaybookgrapher/data/*)

build: $(PACKAGE)

$(PACKAGE): $(SRC)
	@echo "Building the package..."
	@python setup.py bdist_wheel

# Deploy to Pypi Live environment
deploy: clean build
	@echo "Deploying to Pypi Live environment..."
	@twine upload dist/*

# Deploy to Pypi test environment
deploy_test: clean build
	@echo "Deploying to Pypi Test environment..."
	@twine upload --repository-url https://test.pypi.org/legacy/ dist/*

test_install: build
	@./tests/test_install.sh $(VIRTUALENV_DIR) $(ANSIBLE_VERSION)

test:
	cd tests && pytest

clean:
	@echo "Cleaning..."
	rm -rf ansible_playbook_grapher.egg-info build dist $(VIRTUALENV_DIR) tests/htmlcov tests/.pytest_cache .eggs tests/generated-svgs tests/.coverage

.PHONY: clean test_install