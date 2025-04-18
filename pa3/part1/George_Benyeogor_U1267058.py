#!/usr/bin/env python3

import argparse
import subprocess
import sys


def run(cmd, **kw):
    print("> " + " ".join(cmd))
    subprocess.run(cmd, check=True, **kw)

def build_network():
    """Build the network using docker-compose"""
    run(["docker", "compose", "build", "--no-cache"])


def construct_network():
    """Bring up all containers & networks via docker‑compose"""
    run(["docker", "compose", "up", "-d"])
    print("Network constructed. Please wait 30 seconds for OSPF setup to complete.")


def destroy_network():
    """Bring down all containers & networks via docker‑compose"""
    run(["docker", "compose", "down"])


def move_traffic(path):
    """
    Change link costs so that ICMP/TCP traffic follows either:
      - north path:  R1→R2→R3
      - south path:  R1→R4→R3
    """
    if path == "north":
        # make R1→R2 cheap, R1→R4 expensive
        configure_ospf_cost("part1-r1-1", "net15", 5)  # R1→R2 
        configure_ospf_cost("part1-r2-1", "net17", 5)  # R2→R3 
        configure_ospf_cost("part1-r1-1", "net16", 50) # R1→R4
        configure_ospf_cost("part1-r4-1", "net18", 50) # R4→R3

    else:
        # make R1→R4 cheap, R1→R2 expensive
        configure_ospf_cost("part1-r1-1", "net16", 5)  # R1→R2 
        configure_ospf_cost("part1-r4-1", "net18", 5)  # R2→R3 
        configure_ospf_cost("part1-r1-1", "net15", 50) # R1→R4
        configure_ospf_cost("part1-r2-1", "net17", 50) # R4→R3


def configure_ospf_cost(router, interface, cost):
            run(["docker", "exec", router, "vtysh",
             "-c", "configure terminal",
             "-c", f"interface {interface}",
             "-c", f"ip ospf cost {cost}",
             "-c", "end", "-c", "write memory"])


def main():
    p = argparse.ArgumentParser(
         usage="%(prog)s [-h] <command> [options]",
        description="Orchestrator for network traffic movement",
    )
    
    sub = p.add_subparsers(dest="cmd", title="commands", required=True)
    sub.add_parser("construct", help="Bring up containers & Docker networks")
    sub.add_parser("destroy",   help="Bring down containers & Docker networks")
    sub.add_parser("build",     help="Build the network using docker-compose")
    mv = sub.add_parser("move", help="Shift traffic north or south path")
    mv.add_argument("direction", choices=["north", "south"],
                    help="north = R1→R2→R3, south = R1→R4→R3")

    args = p.parse_args()

    if args.cmd == "construct":
        construct_network()
    elif args.cmd == "destroy":
        destroy_network()
    elif args.cmd == "build":
        build_network()
    elif args.cmd == "move":
        move_traffic(args.direction)
    else:
        p.print_help()
        sys.exit(1)

# This is the main entry point for the script
# It allows the script to be run directly or imported as a module
if __name__ == "__main__":
    main()
