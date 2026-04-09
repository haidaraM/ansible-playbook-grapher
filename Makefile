VIRTUALENV_DIR=venv-test-install
PACKAGE := dist/$(shell ls dist 2> /dev/null)
SRC=$(wildcard ansibleplaybookgrapher/*.py pyproject.toml ansibleplaybookgrapher/data/*)

build: $(PACKAGE)

$(PACKAGE): $(SRC)
	@echo "Building the package..."
	@uv build

# Deploy to Pypi Live environment
deploy: clean build
	@echo "Deploying to Pypi Live environment..."
	@uv publish

# Deploy to Pypi test environment
deploy_test: clean build
	@echo "Deploying to Pypi Test environment..."
	@uv publish --publish-url https://test.pypi.org/legacy/

test_install: build
	@./tests/test_install.sh $(VIRTUALENV_DIR) $(ANSIBLE_CORE_VERSION)

lint:
	uv run ruff format
	uv run ruff check --fix

test:
    # Due to some side effects with Ansible, we have to run the tests in a certain order
	cd tests && uv run pytest test_cli.py test_utils.py test_parser.py test_graph_model.py test_graphviz_postprocessor.py test_graphviz_renderer.py test_mermaid_renderer.py test_json_renderer.py

clean:
	@echo "Cleaning..."
	rm -rf ansible_playbook_grapher.egg-info build dist $(VIRTUALENV_DIR) tests/htmlcov tests/.pytest_cache .eggs tests/generated-* tests/.coverage

.PHONY: clean test_install
