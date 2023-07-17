from dataclasses import dataclass, field
from ipaddress import IPv4Network

from wggen.client import WGClient
from wggen.server import WGServer


@dataclass(slots=True)
class SubGroup:
    group: str
    name: str
    subnet: IPv4Network
    file_prefix: str
    peer_count: int
    subgroup_json_override: str | None = None
    configs: list[WGClient] = field(init=False)

    def generate_configs(self, server: WGServer) -> None:
        friendly_json = {
            "group": self.group,
            "subgroup": self.subgroup_json_override or self.name,
        }
        if self.peer_count == 1:
            self.configs = [
                WGClient(
                    server,
                    self.file_prefix,
                    self.subnet[1],
                    friendly_json=friendly_json | {"client": self.file_prefix, "friendly_name": self.file_prefix},
                )
            ]
        else:
            self.configs = [
                WGClient(
                    server,
                    f"{self.file_prefix}{i}",
                    self.subnet[i],
                    friendly_json=friendly_json | {"client": f"{self.file_prefix}{i}", "friendly_name": f"{self.name}_{self.file_prefix}{i}"},
                )
                for i in range(1, self.peer_count + 1)
            ]


@dataclass(slots=True)
class Group:
    name: str
    subnet: IPv4Network
    subgroup_count: int
    subgroup_bits: int
    peers_per_subgroup: int
    file_prefix: str | None = None
    subgroup_json_prefix: str | None = None
    subgroups: list[SubGroup] = field(init=False)

    def __post_init__(self) -> None:
        if self.has_subgroups:
            if self.single_peer_per_subgroup:
                subgroups = [
                    SubGroup(
                        self.name,
                        f"{self.name}{i}",
                        subnet,
                        f"{self.file_prefix}{i}" if self.file_prefix else f"{self.name}{i}",
                        self.peers_per_subgroup,
                        f"{self.subgroup_json_prefix}{i}" if self.subgroup_json_prefix else None,
                    )
                    for i, subnet in zip(
                        range(self.subgroup_count), self.subnet.subnets(new_prefix=self.subgroup_bits), strict=False
                    )
                ]
            else:
                subgroups = [
                    SubGroup(
                        self.name,
                        f"{self.name}{i}",
                        subnet,
                        self.file_prefix or f"{self.name}{i}_",
                        self.peers_per_subgroup,
                        f"{self.subgroup_json_prefix}{i}" if self.subgroup_json_prefix else None,
                    )
                    for i, subnet in zip(
                        range(self.subgroup_count), self.subnet.subnets(new_prefix=self.subgroup_bits), strict=False
                    )
                ]
        else:
            subgroups = [
                SubGroup(self.name, self.name, self.subnet, self.file_prefix or self.name, self.peers_per_subgroup)
            ]
        self.subgroups = subgroups

    @property
    def single_peer_per_subgroup(self) -> bool:
        return self.peers_per_subgroup == 1

    @property
    def has_subgroups(self) -> bool:
        return self.subgroup_count != 1

    def generate_configs(self, server: WGServer) -> None:
        for subgroup in self.subgroups:
            subgroup.generate_configs(server)
