import os

import pytest
from ansible.plugins.loader import init_plugin_loader

from ansibleplaybookgrapher import __prog__
from ansibleplaybookgrapher.cli import PlaybookGrapherCLI
from tests import FIXTURES_DIR, INVENTORY_FILE


@pytest.fixture(name="data_loader")
def fixture_data_loader():
    """Return an Ansible  DataLoader
    :return:
    """
    from ansible.parsing.dataloader import DataLoader

    return DataLoader()


@pytest.fixture(name="inventory_manager")
def fixture_inventory_manager(data_loader):
    """Return an Ansible  InventoryManager
    :return:
    """
    from ansible.inventory.manager import InventoryManager

    return InventoryManager(loader=data_loader, sources=INVENTORY_FILE)


@pytest.fixture(name="variable_manager")
def fixture_variable_manager(data_loader, inventory_manager):
    """Return an Ansible  VariableManager
    :return:
    """
    from ansible.vars.manager import VariableManager

    return VariableManager(loader=data_loader, inventory=inventory_manager)


@pytest.fixture(scope="session", autouse=True)
def display():
    """Return a display
    :return:
    """
    from ansible.utils.display import Display

    display = Display()
    display.verbosity = 3
    return display


@pytest.fixture(scope="session", autouse=True)
def init_ansible_plugin_loader() -> None:
    """Init the Ansible plugin loader responsible to find the collections and stuff
    This init plugin is called in CLI.run but here we are not using that.
    It was called automatically in ansible-core < 2.15 but changed in https://github.com/ansible/ansible/pull/78915
    :return:
    """
    init_plugin_loader()


@pytest.fixture()
def grapher_cli(request) -> PlaybookGrapherCLI:
    """Because Ansible is not designed to be used as a library, we need the CLI everywhere. The CLI is the main entrypoint
    of Ansible, and it sets some global variables that are needed by some classes and methods.
    See this commit: https://github.com/ansible/ansible/commit/afdbb0d9d5bebb91f632f0d4a1364de5393ba17a
    As such, this fixture is just used to init this global context
    :return:
    """
    # The request param should be the path to the playbook
    args_params = request.param.copy()
    # The last item of the args should be the name of the playbook file in the fixtures.
    args_params[-1] = os.path.join(FIXTURES_DIR, args_params[-1])
    cli = PlaybookGrapherCLI([__prog__, *args_params])
    cli.parse()
    return cli
