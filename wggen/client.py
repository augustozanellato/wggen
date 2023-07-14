from ipaddress import IPv4Address, IPv4Interface

from wireguard_tools.wireguard_config import WireguardConfig, WireguardPeer
from wireguard_tools.wireguard_key import WireguardKey

from wggen.server import WGServer


class WGClient:
    def __init__(
        self,
        server: WGServer,
        filename: str,
        address: IPv4Address,
        friendly_name: str | None = None,
        friendly_json: dict | None = None,
    ):
        key = WireguardKey.generate()
        interface = IPv4Interface(address)
        self.name = filename
        self.config = WireguardConfig(private_key=key, addresses=[interface])
        self.config.add_peer(server.peer)
        server.config.add_peer(
            WireguardPeer(
                public_key=key.public_key(),
                allowed_ips=[interface],
                friendly_name=friendly_name,
                friendly_json=friendly_json,
            )
        )
