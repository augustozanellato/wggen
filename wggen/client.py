from ipaddress import IPv4Address, IPv4Interface

from wireguard_tools.wireguard_config import WireguardConfig, WireguardPeer
from wireguard_tools.wireguard_key import WireguardKey

from wggen.server import WGServer


class WGClient:
    def __init__(self, server: WGServer, name: str, address: IPv4Address):
        key = WireguardKey.generate()
        interface = IPv4Interface(address)
        self.name = name
        self.config = WireguardConfig(private_key=key, addresses=[interface])
        self.config.add_peer(server.peer)
        server.config.add_peer(WireguardPeer(public_key=key.public_key(), allowed_ips=[interface]))
