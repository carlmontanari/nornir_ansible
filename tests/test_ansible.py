import os

import pytest
import ruamel.yaml
from nornir.core.exceptions import NornirNoValidInventoryError

from nornir_ansible.inventory import ansible

BASE_PATH = os.path.join(os.path.dirname(__file__), "ansible")


def save(inv_serialized, hosts_file, groups_file, defaults_file):
    yml = ruamel.yaml.YAML(typ="safe")
    yml.default_flow_style = False
    with open(hosts_file, "w+") as f:
        yml.dump(inv_serialized["hosts"], f)
    with open(groups_file, "w+") as f:
        yml.dump(inv_serialized["groups"], f)
    with open(defaults_file, "w+") as f:
        yml.dump(inv_serialized["defaults"], f)


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
        hosts_file = os.path.join(base_path, "expected", "hosts.yaml")
        groups_file = os.path.join(base_path, "expected", "groups.yaml")
        defaults_file = os.path.join(base_path, "expected", "defaults.yaml")

        inv = ansible.AnsibleInventory(
            hostsfile=os.path.join(base_path, "source", "hosts")
        )
        expected_hosts, expected_groups, expected_defaults = read(
            hosts_file, groups_file, defaults_file
        )
        assert inv.hosts == expected_hosts
        assert inv.groups == expected_groups
        assert inv.defaults == expected_defaults

    def test_parse_error(self):
        base_path = os.path.join(BASE_PATH, "parse_error")
        with pytest.raises(NornirNoValidInventoryError):
            ansible.parse(hostsfile=os.path.join(base_path, "source", "hosts"))
