![](https://github.com/carlmontanari/nornir_ansible/workflows/Weekly%20Build/badge.svg)
[![PyPI version](https://badge.fury.io/py/nornir_ansible.svg)](https://badge.fury.io/py/nornir_ansible)
[![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/)
[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/)
[![Python 3.8](https://img.shields.io/badge/python-3.8-blue.svg)](https://www.python.org/downloads/release/python-380/)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)


nornir ansible
==============

Ansible Inventory plugin for [nornir](https://github.com/nornir-automation/nornir).


# Install

In most cases installation via pip is the simplest and best way to install nornir_ansible.

```
pip install nornir_ansible
```


# Basic Example

In your nornir configuration, set the inventory plugin value to `AnsibleInventory`

```yaml
---
inventory:
  plugin: AnsibleInventory
  options:
    hostsfile: "inventory.yaml"
```

The `hostsfile` inventory option argument should point to a valid Ansible inventory file, in this case a yaml style
 inventory such as:

```yaml
---
all:
  vars:
    ansible_python_interpreter: "/usr/bin/python3"
    username: "vrnetlab"
    password: "VR-netlab9"
  children:
    sea:
      hosts:
        sea-eos-1:
          ansible_host: "172.18.0.14"
        sea-nxos-1:
          ansible_host: "172.18.0.12"
      children:
        arista-eos:
          hosts:
            sea-eos-1:
          vars:
            platform: "eos"
        cisco-nxos:
          hosts:
            sea-nxos-1:
          vars:
            platform: "nxos"
```

Initialize your nornir object and validate the appropriate inventory plugin was loaded, and the inventory file was
 parsed:

```python
>>> from nornir import InitNornir
>>> nr = InitNornir(config_file="config.yaml")
>>> print(nr.config.inventory.plugin)
<class 'nornir_ansible.plugins.inventory.ansible.AnsibleInventory'>
>>> print(nr.inventory.hosts)
{'sea-eos-1': Host: sea-eos-1, 'sea-nxos-1': Host: sea-nxos-1}
>>>
```

# Useful Links

- [Nornir](https://github.com/nornir-automation/nornir)
- [Nornir Discourse Group](https://nornir.discourse.group)
- [Ansible Inventory Documentation](https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html)
- [An Introduction to Nornir Blog](https://pynet.twb-tech.com/blog/nornir/intro.html)
- [Nornir using an Ansible Inventory Blog](https://pynet.twb-tech.com/blog/nornir/nornir-ansible-inventory-p1.html)
