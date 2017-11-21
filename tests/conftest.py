import pytest

from ansibleplaybookgrapher.grapher import Grapher
from tests import INVENTORY_FILE


@pytest.fixture(name='data_loader')
def fixture_data_loader():
    """
    Return an Ansible  DataLoader
    :return:
    """
    from ansible.parsing.dataloader import DataLoader
    return DataLoader()


@pytest.fixture(name='inventory_manager')
def fixture_inventory_manager(data_loader):
    """
    Return an Ansible  InventoryManager
    :return:
    """
    from ansible.inventory.manager import InventoryManager
    return InventoryManager(loader=data_loader, sources=INVENTORY_FILE)


@pytest.fixture(name='variable_manager')
def fixture_variable_manager(data_loader, inventory_manager):
    """
    Return an Ansible  VariableManager
    :return:
    """
    from ansible.vars.manager import VariableManager
    return VariableManager(loader=data_loader, inventory=inventory_manager)


@pytest.fixture(name='grapher')
def fixture_simple_grapher(data_loader, inventory_manager, variable_manager, request):
    return Grapher(data_loader=data_loader, inventory_manager=inventory_manager, variable_manager=variable_manager,
                   playbook_filename=request.param)
