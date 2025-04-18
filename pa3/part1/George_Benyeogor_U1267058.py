#!/usr/bin/env python3

import argparse
import subprocess
import sys


class HelpOnErrorParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_help(sys.stderr)
        self.exit(2, f"\n{self.prog}: error: {message}\n")


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
        configure_ospf_cost("part1-r3-1", "net17", 5)  # R3→R2 
        configure_ospf_cost("part1-r2-1", "net15", 5)  # R2→R1
 
        configure_ospf_cost("part1-r1-1", "net16", 50) # R1→R4
        configure_ospf_cost("part1-r4-1", "net18", 50) # R4→R3
        configure_ospf_cost("part1-r3-1", "net18", 50) # R3→R4 
        configure_ospf_cost("part1-r4-1", "net16", 50) # R4→R1


    else:
        # make R1→R4 cheap, R1→R2 expensive
        configure_ospf_cost("part1-r1-1", "net16", 5)  # R1→R4 
        configure_ospf_cost("part1-r4-1", "net18", 5)  # R4→R3
        configure_ospf_cost("part1-r3-1", "net18", 5)  # R3→R4
        configure_ospf_cost("part1-r4-1", "net16", 5)  # R4→R1


        configure_ospf_cost("part1-r1-1", "net15", 50) # R1→R4
        configure_ospf_cost("part1-r2-1", "net17", 50) # R4→R3
        configure_ospf_cost("part1-r3-1", "net17", 50) # R3→R2
        configure_ospf_cost("part1-r2-1", "net15", 50) # R2→R1


def configure_ospf_cost(router, interface, cost):
    """
    Configure the OSPF cost for a given interface on a router.
    This function uses vtysh to run the OSPF configuration commands inside the container.   
    """
    # Run the vtysh command inside the router container to configure OSPF cost
    run(["docker", "exec", router, "vtysh",
        "-c", "configure terminal",
        "-c", f"interface {interface}",
        "-c", f"ip ospf cost {cost}",
        "-c", "end", "-c", "write memory"])


def main():
    p = HelpOnErrorParser(
         usage="%(prog)s [-h] <command> [options]",
        description="Orchestrator for network traffic movement",
    )
    
    sub = p.add_subparsers(dest="cmd", title="commands", required=True)
    
    build = sub.add_parser("build", aliases=["b"], help="Bring up containers & Docker networks")
    build.set_defaults(func=lambda _: build_network())

    destroy = sub.add_parser("destroy", aliases=["d"], help="Bring down containers & Docker networks")
    destroy.set_defaults(func=lambda _: destroy_network())

    construct = sub.add_parser("construct", aliases=["c"], help="Bring up containers & Docker networks")
    construct.set_defaults(func=lambda _: construct_network())

    mv = sub.add_parser("move", aliases=["m"], help="Shift traffic north or south path")
    mv.add_argument("direction", choices=["north","south"], help="north = R1→R2→R3, south = R1→R4→R3")
    mv.set_defaults(func=lambda ns: move_traffic(ns.direction))

    args = p.parse_args()
    args.func(args)

   

# This is the main entry point for the script
# It allows the script to be run directly or imported as a module
if __name__ == "__main__":
    main()
