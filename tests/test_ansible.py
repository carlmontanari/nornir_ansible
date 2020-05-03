import os

import pytest
import ruamel.yaml
from nornir.core.exceptions import NornirNoValidInventoryError
from nornir_utils.plugins.inventory import simple

from nornir_ansible.plugins.inventory import ansible

BASE_PATH = os.path.join(os.path.dirname(__file__), "ansible")


def read(hosts_file, groups_file, defaults_file):
    yml = ruamel.yaml.YAML(typ="safe")
    with open(hosts_file, "r") as f:
        hosts = yml.load(f)
    with open(groups_file, "r") as f:
        groups = yml.load(f)
    with open(defaults_file, "r") as f:
        defaults = yml.load(f)
    return hosts, groups, defaults


class Test(object):
    @pytest.mark.parametrize("case", ["ini", "yaml", "yaml2", "yaml3"])
    def test_inventory(self, case):
        base_path = os.path.join(BASE_PATH, case)
        expected_hosts_file = os.path.join(base_path, "expected", "hosts.yaml")
        expected_groups_file = os.path.join(base_path, "expected", "groups.yaml")
        expected_defaults_file = os.path.join(base_path, "expected", "defaults.yaml")

        inv = ansible.AnsibleInventory(hostsfile=os.path.join(base_path, "source", "hosts"))
        expected_hosts, expected_groups, expected_defaults = read(
            expected_hosts_file, expected_groups_file, expected_defaults_file
        )
        assert inv.hosts == expected_hosts
        assert inv.groups == expected_groups
        assert inv.defaults == expected_defaults

        serialized_inv = inv.load()
        control_inv = simple.SimpleInventory(
            host_file=expected_hosts_file,
            group_file=expected_groups_file,
            defaults_file=expected_defaults_file,
        )
        serialized_control_inv = control_inv.load()
        assert serialized_inv.dict() == serialized_control_inv.dict()

    def test_parse_error(self):
        base_path = os.path.join(BASE_PATH, "parse_error")
        with pytest.raises(NornirNoValidInventoryError):
            ansible.parse(hostsfile=os.path.join(base_path, "source", "hosts"))
