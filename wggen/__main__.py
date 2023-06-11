#!/usr/bin/env python3

import argparse
import sys
from ipaddress import IPv4Network
from pathlib import Path

from wggen.group import Group
from wggen.server import WGServer

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Wireguard configuration files")

    parser.add_argument(
        "--server",
        type=str,
        metavar="example.com",
        help="Server public address",
        required=True,
    )
    parser.add_argument(
        "--server-port",
        type=int,
        metavar="N",
        default=51820,
        help="Wireguard listen port (default 51820)",
    )
    parser.add_argument(
        "--teams-subnet",
        type=str,
        metavar="0.0.0.0/0",
        default="10.80.0.0/16",
        help="Player subnet, will be split in a /24 per team. (Defaults to 10.80.0.0/16)",
    )
    parser.add_argument(
        "--vulnboxes-subnet",
        type=str,
        metavar="0.0.0.0/0",
        default="10.60.0.0/16",
        help="Vulnboxes subnet, will be split in a /24 per team, with .1 being the teams vulnbox. "
        "(Defaults to 10.60.0.0/16)",
    )
    parser.add_argument(
        "--gamesystem-subnet",
        type=str,
        metavar="0.0.0.0/0",
        default="10.10.0.0/24",
        help="Gamesystem subnet, GS will be at .1 (Defaults to 10.10.0.0/24)",
    )
    parser.add_argument(
        "--jury-subnet",
        type=str,
        metavar="0.0.0.0/0",
        default="10.10.10.0/24",
        help="Jury subnet. (Defaults to 10.10.10.0/24)",
    )
    parser.add_argument(
        "--jury-count",
        type=int,
        metavar="N",
        default="8",
        help="Jury profile count. (Defaults to 8)",
    )
    parser.add_argument(
        "--router-ip",
        type=str,
        metavar="0.0.0.0",
        default="10.254.0.1",
        help="Router ip address. (Defaults to 10.254.0.1)",
    )
    parser.add_argument("--team-count", type=int, metavar="N", required=True)
    parser.add_argument(
        "--team-size",
        type=int,
        metavar="N",
        default=8,
    )

    parser.add_argument("--output-dir", type=str, help="A path to dump configs to", required=True)

    args = parser.parse_args()
    team_network = IPv4Network(args.teams_subnet)
    vulnbox_network = IPv4Network(args.vulnboxes_subnet)
    gamesystem_network = IPv4Network(args.gamesystem_subnet)
    jury_network = IPv4Network(args.jury_subnet)

    groups = [
        Group("team", team_network, args.team_count + 1, 24, args.team_size, "player"),
        Group("vulnbox", vulnbox_network, args.team_count + 1, 24, 1, "vulnbox-team"),
        Group("gamesystem", gamesystem_network, 1, 24, 1),
        Group("jury", jury_network, 1, 24, args.jury_count),
    ]
    server = WGServer(args.server, args.server_port, args.router_ip)
    for group in groups:
        server.add_subnet(group.subnet)
    for group in groups:
        group.generate_configs(server)

    out_dir = Path(args.output_dir)
    if not out_dir.exists():
        Path.mkdir(out_dir)
    if not out_dir.is_dir():
        print(f"Error! {out_dir} is not a directory")
        sys.exit(1)

    if next(out_dir.iterdir(), None):
        print(f"Error! {out_dir} is not empty")
        sys.exit(1)

    server_config_path = out_dir / "server.conf"
    with server_config_path.open("w") as f:
        f.write(server.config.to_wgconfig(wgquick_format=True))

    for group in groups:
        group_path = out_dir / group.prefix
        group_path.mkdir()
        for subgroup in group.subgroups:
            subgroup_path = (
                (group_path / subgroup.name)
                if group.has_subgroups and not group.single_peer_per_subgroup
                else group_path
            )
            subgroup_path.mkdir(exist_ok=True)
            for client in subgroup.configs:
                client_path = subgroup_path / f"{client.name}.conf"
                with client_path.open("w") as conf:
                    conf.write(client.config.to_wgconfig(wgquick_format=True))
