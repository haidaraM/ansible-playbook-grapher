ANSIBLE_VERSION=2.9
VIRTUALENV_DIR=venv
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
	@./test_install.sh $(VIRTUALENV_DIR) $(ANSIBLE_VERSION)

test:
	# Ansible 2.8 CLI sets some global variables causing the tests to fail if the cli tests are run before
	# the grapher tests. It works in Ansible 2.9. So here we explicitly set the tests order.
	# TODO: Remove pytest arguments when we drop support for Ansible 2.8
	cd tests && pytest test_grapher.py test_cli.py test_postprocessor.py

clean:
	@echo "Cleaning..."
	rm -rf ansible_playbook_grapher.egg-info build dist $(VIRTUALENV_DIR) tests/htmlcov tests/.pytest_cache .eggs tests/generated_svg tests/.coverage

.PHONY: clean test_install