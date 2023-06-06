#!/usr/bin/env python3

import argparse
import os
import re
import sys
from math import log10
from pathlib import Path

from wggen.generation import WGGenerator

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
        "--server-number",
        type=int,
        metavar="N",
        default=0,
        help="Server number when using with multiple servers (default 0)",
    )

    peer_group = parser.add_mutually_exclusive_group()
    peer_group.add_argument(
        "--per-group",
        type=int,
        default=2,
        metavar="N",
        help="Number of clients per one group (or subnet) (default 2)",
    )
    peer_group.add_argument(
        "--single-peer",
        action="store_true",
        help="Force a single peer in each group (/32 subnet)",
    )

    parser.add_argument(
        "--subnet",
        type=str,
        default="10.60.0.0/16",
        metavar="0.0.0.0/0",
        help="Main subnet to add groups to (default 10.60.0.0/16)",
    )
    parser.add_argument(
        "--subnet-newbits",
        type=int,
        default=8,
        metavar="N",
        help="Number of bits for group subnet in base subnet (default 8)",
    )
    parser.add_argument(
        "--routes",
        type=str,
        default="10.0.0.0/8",
        metavar="0.0.0.0/0,192.168.1.0/24",
        help="Comma-separated list of subnets to route through VPN on clients (default 10.0.0.0/8)",
    )

    parser.add_argument(
        "--group-name",
        type=str,
        default="group",
        metavar="NAME",
        help='Name of the group (e.g. "team") for peer comment (default "group")',
    )

    parser.add_argument("--server-output", type=str, help="A path to dump configs to", required=True)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--groups", type=int, metavar="N", help="Group count")
    group.add_argument("--range", type=str, metavar="N-N", help="Range of group numbers (inclusive)")
    group.add_argument("--list", type=str, metavar="N,N,...", help="List of group numbers")

    args = parser.parse_args()

    groups = None
    if args.groups:
        groups = list(range(args.groups))
    elif args.range:
        match = re.search(r"(\d+)-(\d+)", args.range)
        if not match:
            print("Invalid range")
            sys.exit(1)

        groups = list(range(int(match.group(1)), int(match.group(2)) + 1))
    else:
        groups = list(map(int, args.list.split(",")))

    generator = WGGenerator(
        server=args.server,
        server_number=args.server_number,
        per_group=args.per_group,
        group_list=groups,
        single_peer=args.single_peer,
        subnet=args.subnet,
        subnet_newbits=args.subnet_newbits,
        routed_subnets=args.routes,
        group_name=args.group_name,
    )

    so_dir = Path(args.server_output)
    if not so_dir.exists():
        Path.mkdir(so_dir)
    if not so_dir.is_dir():
        print(f"Error! {so_dir} is not a directory")
        sys.exit(1)

    if next(so_dir.iterdir(), None):
        print(f"Error! {so_dir} is not empty")
        sys.exit(1)

    server_config_path = so_dir / f"server{args.server_number}.conf"
    with server_config_path.open("w") as f:
        f.write(generator.server_config.dumps())
    if args.single_peer:
        group_config_dir = so_dir / f"{args.group_name}"
        group_config_dir.mkdir()
        for group in groups:
            justified_groups = str(group).rjust(int(log10(len(groups))) + 1, "0")
            peer_config_path = group_config_dir / f"{args.group_name}{justified_groups}.conf"
            with peer_config_path.open("w") as f:
                conf = generator.peer_configs[group][0]
                f.write(conf.dumps())
    else:
        for group in groups:
            justified_groups = str(group).rjust(int(log10(len(groups))) + 1, "0")
            group_config_dir = so_dir / f"{args.group_name}{justified_groups}"
            group_config_dir.mkdir()
            group_configs = generator.peer_configs[group]
            for peer, conf in group_configs.items():
                justified_peer = str(peer + 1).rjust(int(log10(len(group_configs))) + 1, "0")
                peer_config_path = Path(group_config_dir) / f"{args.group_name}{justified_groups}_{justified_peer}.conf"
                with peer_config_path.open("w") as f:
                    f.write(conf.dumps())
