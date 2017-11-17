import pytest

from tests import INVENTORY_FILE


@pytest.fixture(name='data_loader')
def fixture_data_loader():
    from ansible.parsing.dataloader import DataLoader
    return DataLoader()


@pytest.fixture(name='inventory_manager')
def fixture_inventory_manager(data_loader):
    from ansible.inventory.manager import InventoryManager
    return InventoryManager(loader=data_loader, sources=INVENTORY_FILE)


@pytest.fixture(name='variable_manager')
def fixture_variable_manager(data_loader, inventory_manager):
    from ansible.vars.manager import VariableManager
    return VariableManager(loader=data_loader, inventory=inventory_manager)
