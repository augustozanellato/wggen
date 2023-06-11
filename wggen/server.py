from functools import cached_property
from ipaddress import IPv4Interface, IPv4Network, IPv6Interface

from wireguard_tools.wireguard_config import WireguardConfig, WireguardPeer
from wireguard_tools.wireguard_key import WireguardKey


class WGServer:
    def __init__(self, domain: str, listen_port: int, address: str):
        key = WireguardKey.generate()
        internal_interface = IPv4Interface(address)
        self.domain = domain
        self.config = WireguardConfig(private_key=key, listen_port=listen_port, addresses=[internal_interface])
        self.public_key = key.public_key()
        self.subnets: list[IPv4Interface | IPv6Interface] = [internal_interface]

    def add_subnet(self, subnet: IPv4Network) -> None:
        self.subnets.append(IPv4Interface(subnet))

    @cached_property
    def peer(self) -> WireguardPeer:
        return WireguardPeer(
            self.public_key,
            endpoint_host=self.domain,
            endpoint_port=self.config.listen_port,
            persistent_keepalive=5,
            allowed_ips=self.subnets,
        )
