"""nornir_ansible.inventory.ansible"""
import configparser as cp
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, DefaultDict, Dict, List, MutableMapping, Optional, Tuple, Type, Union, cast

import ruamel.yaml
from mypy_extensions import TypedDict
from nornir.core.exceptions import NornirNoValidInventoryError
from nornir.core.inventory import (
    ConnectionOptions,
    Defaults,
    Group,
    Host,
    HostOrGroup,
    Inventory,
    ParentGroups,
)
from ruamel.yaml.composer import ComposerError
from ruamel.yaml.scanner import ScannerError

VARS_FILENAME_EXTENSIONS = ["", ".ini", ".yml", ".yaml"]
RESERVED_FIELDS = ("hostname", "port", "username", "password", "platform", "connection_options")
YAML = ruamel.yaml.YAML(typ="safe")
LOG = logging.getLogger(__name__)

VarsDict = Dict[str, Any]
AnsibleHostsDict = Dict[str, Optional[VarsDict]]

AnsibleGroupDataDict = TypedDict(
    "AnsibleGroupDataDict",
    {"children": Dict[str, Any], "vars": VarsDict, "hosts": AnsibleHostsDict},
    total=False,
)  # bug: https://github.com/python/mypy/issues/5357

AnsibleGroupsDict = Dict[str, AnsibleGroupDataDict]


class AnsibleParser:
    def __init__(self, hostsfile: str) -> None:
        """
        Parse Ansible inventories for use with Nornir

        Arguments:
            hostsfile: Path to valid Ansible inventory

        """
        self.hostsfile = hostsfile
        self.path = str(Path(hostsfile).absolute().parents[0])
        self.hosts: Dict[str, Any] = {}
        self.groups: Dict[str, Any] = {}
        self.defaults: Dict[str, Any] = {"data": {}}
        self.original_data: Optional[AnsibleGroupsDict] = None
        self.load_hosts_file()

    def parse_group(
        self, group: str, data: AnsibleGroupDataDict, parent: Optional[str] = None
    ) -> None:
        """
        Parse inventory group data

        Arguments:
            group: name of group being parsed
            data: inventory data for the group
            parent: optional parent of group

        """
        data = data or {}
        if group == "defaults":
            group_file = "all"
            dest_group = self.defaults
        else:
            self.add(group, self.groups)
            group_file = group
            dest_group = self.groups[group]

        if parent and parent != "defaults":
            dest_group["groups"].append(parent)

        group_data = data.get("vars", {})

        vars_file_data = {}
        if self._vars_file_exists(f"{self.path}/group_vars/{group_file}"):
            vars_file_data = self.read_vars_file(
                element=group_file, path=self.path, is_host=False, is_dir=False
            )
        elif Path(f"{self.path}/group_vars/{group_file}").is_dir():
            for file in self._get_all_files(f"{self.path}/group_vars/{group_file}"):
                t_vars_file_data = self.read_vars_file(
                    element=group_file,
                    path=file,
                    is_host=False,
                    is_dir=True,
                )
                if isinstance(t_vars_file_data, dict):
                    vars_file_data = {**t_vars_file_data, **vars_file_data}

        self.normalize_data(dest_group, group_data, vars_file_data)
        self.map_nornir_vars(dest_group)

        self.parse_hosts(data.get("hosts", {}), parent=group)

        for children, children_data in data.get("children", {}).items():
            self.parse_group(children, cast(AnsibleGroupDataDict, children_data), parent=group)

    def parse(self) -> None:
        """Parse inventory entrypoint"""
        if self.original_data is not None:
            self.parse_group("defaults", self.original_data["all"])
        self.sort_groups()

    def parse_hosts(self, hosts: AnsibleHostsDict, parent: Optional[str] = None) -> None:
        """
        Parse inventory hosts

        Arguments:
            hosts: dict containing hosts; {host: data}
            parent: optional parent of host

        """
        for host, data in hosts.items():
            data = data or {}
            self.add(host, self.hosts)
            if parent and parent != "defaults":
                self.hosts[host]["groups"].append(parent)

            vars_file_data = {}
            if self._vars_file_exists(f"{self.path}/host_vars/{host}"):
                vars_file_data = self.read_vars_file(
                    element=host, path=self.path, is_host=True, is_dir=False
                )

            elif Path(f"{self.path}/host_vars/{host}").is_dir():
                vars_file_data = {}
                for file in self._get_all_files(f"{self.path}/host_vars/{host}"):
                    t_vars_file_data = self.read_vars_file(
                        element=host,
                        path=file,
                        is_host=True,
                        is_dir=True,
                    )
                    if isinstance(t_vars_file_data, dict):
                        vars_file_data = {**t_vars_file_data, **vars_file_data}

            self.normalize_data(self.hosts[host], data, vars_file_data, host)
            self.map_nornir_vars(self.hosts[host])

    @staticmethod
    def _get_all_files(path: str) -> List[str]:
        """
        Get all files with VARS_FILENAME_EXTENSIONS, contains in path/ and subdirectories

        Args:
            path: Path to directory

        Returns:
            files_lst: List of files that are in this directory and subdirectories

        """
        files_list = [
            str(file)
            for file in Path(path).rglob("*")
            if Path(file).suffix in VARS_FILENAME_EXTENSIONS and Path(file).is_file()
        ]

        return files_list

    @staticmethod
    def _vars_file_exists(path: str) -> bool:
        """
        With VARS_FILENAME_EXTENSIONS, check if the file given in parameter exists.

        Args:
            path: Path to file (without extension)

        Returns:
            bool: True if a file exists with of of the extension

        """
        for ext in VARS_FILENAME_EXTENSIONS:
            if Path(f"{path}{ext}").is_file():
                return True
        return False

    def normalize_data(
        self,
        host_or_group: Dict[str, Any],
        data: Dict[str, Any],
        vars_data: Dict[str, Any],
        hostname: Optional[str] = None,
    ) -> None:
        """
        Parse inventory hosts

        data and vars_data come from the inventory file(s) and are generally global/host/group vars
        depending on which section of the inventory file is being currently parsed

        Arguments:
            host_or_group: dict of host or group data
            data: dict of vars to parse
            vars_data: dict of vars to parse

        """
        self.map_nornir_vars(data)
        for k, v in data.items():
            if k in RESERVED_FIELDS:
                host_or_group[k] = v
            else:
                host_or_group["data"][k] = v
        self.map_nornir_vars(vars_data)
        for k, v in vars_data.items():
            if k in RESERVED_FIELDS:
                host_or_group[k] = v
            else:
                host_or_group["data"][k] = v
        for field in RESERVED_FIELDS:
            if field not in host_or_group:
                if field == "connection_options":
                    host_or_group[field] = {}
                elif field == "hostname" and hostname is not None:
                    host_or_group[field] = hostname
                else:
                    host_or_group[field] = None

    def sort_groups(self) -> None:
        """Sort group data"""
        for host in self.hosts.values():
            host["groups"].sort()

        for name, group in self.groups.items():
            if name == "defaults":
                continue

            group["groups"].sort()

    @staticmethod
    def read_vars_file(
        element: str, path: str, is_host: bool = True, is_dir: bool = False
    ) -> VarsDict:
        """
        Read vars file data, return `VarsDict`

        Arguments:
            element: inventory element being parsed, i.e. name of host or group being parsed
            path: parent directory of inventory file
            is_host: bool indicating if reading a host vars file or if false a group vars file
            is_dir: bool indicating if variables are defined in a directory

        """
        sub_dir = "host_vars" if is_host else "group_vars"
        vars_dir = Path(path) / sub_dir

        if is_dir:
            with open(path, "r", encoding="utf-8") as f:
                for ext in VARS_FILENAME_EXTENSIONS:
                    if Path(f"{path}{ext}").is_file():
                        LOG.debug("AnsibleInventory: reading var file %r", path)
                        return cast(Dict[str, Any], YAML.load(f))

        elif vars_dir.is_dir():
            vars_file_base = vars_dir / element
            for extension in VARS_FILENAME_EXTENSIONS:
                vars_file = vars_file_base.with_suffix(vars_file_base.suffix + extension)
                if vars_file.is_file():
                    with open(vars_file, "r", encoding="utf-8") as f:
                        LOG.debug("AnsibleInventory: reading var file %r", vars_file)
                        return cast(Dict[str, Any], YAML.load(f))
            LOG.debug(
                "AnsibleInventory: no vars file was found with the path %r "
                "and one of the supported extensions: %s",
                vars_file_base,
                VARS_FILENAME_EXTENSIONS,
            )
        return {}

    @staticmethod
    def map_nornir_vars(obj: VarsDict) -> None:
        """
        Map ansible-specific variables such as host to nornir equivalent

        Arguments:
            obj: dict of variables being parsed to determine if any of them should be mapped to
                nornir's "core" vars such as username/port

        """
        mappings = {
            "ansible_host": "hostname",
            "ansible_port": "port",
            "ansible_user": "username",
            "ansible_password": "password",
        }
        for ansible_var, nornir_var in mappings.items():
            if ansible_var in obj:
                obj[nornir_var] = obj.pop(ansible_var)

    @staticmethod
    def add(element: str, element_dict: Dict[str, VarsDict]) -> None:
        """
        Determine if host/group is already in vars dict, if not add the host/group

        Arguments:
            element: host or group being parsed
            element_dict: dictionary representing host/group: vars mapping

        """
        if element not in element_dict:
            element_dict[element] = {"groups": [], "data": {}}

    def load_hosts_file(self) -> None:
        """Parse host specific inventory files"""
        raise NotImplementedError


class INIParser(AnsibleParser):
    @staticmethod
    def normalize_value(value: str) -> Union[str, int]:
        """
        Convert integers as strings to actual integers, otherwise return original string

        Arguments:
            value: value to try to cast to int

        """
        try:
            return int(value)

        except (ValueError, TypeError):
            return value

    @staticmethod
    def normalize_content(content: str) -> VarsDict:
        """
        Normalize INI data into a `VarsDict`

        Arguments:
            content: string row from ini inventory file to parse

        """
        result: VarsDict = {}

        if not content:
            return result

        for option in content.split():
            key, value = option.split("=")
            result[key] = INIParser.normalize_value(value)
        return result

    @staticmethod
    def process_meta(meta: Optional[str], section: MutableMapping[str, str]) -> Dict[str, Any]:
        """
        Process ini inventory meta sections such as "children" and "vars"

        Arguments:
            meta: string name of meta; i.e. "children" or "vars"
            section: configparser section to process

        """
        if meta == "vars":
            return {key: INIParser.normalize_value(value) for key, value in section.items()}

        if meta == "children":
            return {group_name: {} for group_name in section}

        raise ValueError(f"Unknown tag {meta}")

    def normalize(self, data: cp.ConfigParser) -> Dict[str, AnsibleGroupDataDict]:
        """
        Parent method to normalize INI vars file into Nornir friendly structure

        Arguments:
            data: configparser parsed ini file data

        """
        groups: DefaultDict[str, Dict[str, Any]] = defaultdict(dict)
        # Dict[str, AnsibleGroupDataDict] does not work because of
        # https://github.com/python/mypy/issues/5359
        result: Dict[str, Dict[str, Dict[str, Dict[str, Any]]]] = {"all": {"children": groups}}

        for section_name, section in data.items():

            if section_name == "DEFAULT":
                continue

            if ":" in section_name:
                group_name, meta = section_name.split(":")
                subsection = self.process_meta(meta, section)
                if group_name == "all":
                    result["all"][meta] = subsection
                else:
                    groups[group_name][meta] = subsection
            else:
                groups[section_name]["hosts"] = {
                    host: self.normalize_content(host_vars) for host, host_vars in section.items()
                }
        return cast(AnsibleGroupsDict, result)

    def load_hosts_file(self) -> None:
        """Parse host specific inventory files"""
        original_data = cp.ConfigParser(interpolation=None, allow_no_value=True, delimiters=" =")
        original_data.read(self.hostsfile)
        self.original_data = self.normalize(original_data)


class YAMLParser(AnsibleParser):
    def load_hosts_file(self) -> None:
        """Parse host specific inventory files"""
        with open(self.hostsfile, "r", encoding="utf-8") as f:
            self.original_data = cast(AnsibleGroupsDict, YAML.load(f))


def parse(hostsfile: str) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    Parse provided inventory file

    Arguments:
        hostsfile: string of hostsfile to parse

    """
    try:
        parser: AnsibleParser = INIParser(hostsfile)
    except cp.Error:
        try:
            parser = YAMLParser(hostsfile)
        except (ScannerError, ComposerError) as exc:
            LOG.error("AnsibleInventory: file %r is not INI or YAML file", hostsfile)
            raise NornirNoValidInventoryError(
                f"AnsibleInventory: no valid inventory source(s) to parse. Tried: {hostsfile}"
            ) from exc
    parser.parse()
    return parser.hosts, parser.groups, parser.defaults


def _get_connection_options(data: Dict[str, Any]) -> Dict[str, ConnectionOptions]:
    """
    Get connection option information for a given host/group

    Arguments:
        data: dictionary of connection options for host/group

    """
    connection_options = {}
    for connection_name, connection_data in data.items():
        connection_options[connection_name] = ConnectionOptions(
            hostname=connection_data.get("hostname"),
            port=connection_data.get("port"),
            username=connection_data.get("username"),
            password=connection_data.get("password"),
            platform=connection_data.get("platform"),
            extras=connection_data.get("extras"),
        )
    return connection_options


def _get_defaults(data: Dict[str, Any]) -> Defaults:
    """
    Get defaults information for a given host/group

    Arguments:
        data: dictionary of defaults data

    """
    return Defaults(
        hostname=data.get("hostname"),
        port=data.get("port"),
        username=data.get("username"),
        password=data.get("password"),
        platform=data.get("platform"),
        data=data.get("data"),
        connection_options=_get_connection_options(data.get("connection_options", {})),
    )


def _get_inventory_element(
    typ: Type[HostOrGroup], data: Dict[str, Any], name: str, defaults: Defaults
) -> HostOrGroup:
    """
    Get inventory information for a given host/group

    Arguments:
        data: dictionary of host or group data to serialize

    """
    return typ(
        name=name,
        hostname=data.get("hostname"),
        port=data.get("port"),
        username=data.get("username"),
        password=data.get("password"),
        platform=data.get("platform"),
        data=data.get("data"),
        groups=data.get("groups"),
        defaults=defaults,
        connection_options=_get_connection_options(data.get("connection_options", {})),
    )


class AnsibleInventory:
    def __init__(
        self,
        hostsfile: str = "hosts",
    ) -> None:
        """
        Ansible Inventory plugin supporting ini and yaml inventory sources.

        Arguments:
            hostsfile: Path to valid Ansible inventory

        """
        self.hosts, self.groups, self.defaults = parse(hostsfile)

    def load(self) -> Inventory:
        """Return nornir Inventory object."""
        serialized_defaults = _get_defaults(self.defaults)

        serialized_hosts = {}
        for host_name, host_data in self.hosts.items():
            serialized_hosts[host_name] = _get_inventory_element(
                Host, host_data, host_name, serialized_defaults
            )

        serialized_groups = {}
        for group_name, group_data in self.groups.items():
            serialized_groups[group_name] = _get_inventory_element(
                Group, group_data, group_name, serialized_defaults
            )

        for h in serialized_hosts.values():
            h.groups = ParentGroups([serialized_groups[g] for g in h.groups])  # type: ignore

        for g in serialized_groups.values():
            g.groups = ParentGroups([serialized_groups[g] for g in g.groups])  # type: ignore

        return Inventory(
            hosts=serialized_hosts,  # type: ignore
            groups=serialized_groups,  # type: ignore
            defaults=serialized_defaults,
        )

    def dict(self) -> Dict[str, Any]:
        """
        Return serialized dictionary of inventory
        """
        return {
            "hosts": {n: h.dict() for n, h in self.hosts.items()},
            "groups": {n: g.dict() for n, g in self.groups.items()},
            "defaults": self.defaults,
        }
