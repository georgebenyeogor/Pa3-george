import argparse
import subprocess
import sys

ROUTERS = ["part1-r1-1", "part1-r2-1", "part1-r3-1", "part1-r4-1"]
HOSTS   = ["part1-ha-1", "part1-hb-1"]


def run(cmd, **kw):
    print("> " + " ".join(cmd))
    subprocess.run(cmd, check=True, **kw)

def construct_network():
    """Bring up all containers & networks via docker‑compose"""
    run(["docker", "compose", "up", "-d"])


def start_ospf():
    """
    For each router, restart FRR and verify ospfd is running.
    """
    for r in ROUTERS:
        run(["docker", "exec", "-it", r, "service", "frr", "restart"])
        run(["docker", "exec", "-it", r, "ps", "-ef", "|", "grep", "[o]spf"])   


def install_host_routes():
    """
    Install default routes on HostA and HostB pointing to the router they attach to.
    Adjust the gateway IP as needed.
    """

    # HostA → R1's IP on net14
    run(["docker", "exec", "-it", "part1-ha-1", 
         "ip", "route", "add", "default", "via", "10.0.14.4"])
    # HostB → R3's IP on net19
    run(["docker", "exec", "-it", "part1-hb-1",
         "ip", "route", "add", "default", "via", "10.0.19.4"])


def move_traffic(path):
    """
    Change link costs so that ICMP/TCP traffic follows either:
      - north path:  R1→R2→R3
      - south path:  R1→R4→R3
    """
    if path == "north":
        # make R1→R2 cheap, R1→R4 expensive
        run(["docker","exec","part1-r1-1","vtysh",
             "-c","configure terminal",
             "-c","interface eth1",   # R1→R2
             "-c","ip ospf cost 5",
             "-c","end","-c","write memory"])
        run(["docker","exec","part1-r1-1","vtysh",
             "-c","configure terminal",
             "-c","interface eth0",   # R1→R4
             "-c","ip ospf cost 50",
             "-c","end","-c","write memory"])
        # repeat on R3, R2, R4 as needed
    else:
        # south path: cheap R1→R4, expensive R1→R2
        run(["docker","exec","part1-r1-1","vtysh",
             "-c","configure terminal",
             "-c","interface eth0",   # R1→R4
             "-c","ip ospf cost 5",
             "-c","end","-c","write memory"])
        run(["docker","exec","part1-r1-1","vtysh",
             "-c","configure terminal",
             "-c","interface eth1",   # R1→R2
             "-c","ip ospf cost 50",
             "-c","end","-c","write memory"])
        # repeat on R3, R2, R4 as needed


def main():
    p = argparse.ArgumentParser(
        description="Orchestrator for network traffic movement"
    )
    
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("construct", help="Bring up containers & Docker networks")
    sub.add_parser("ospf",      help="(Re)start OSPF daemons on routers")
    sub.add_parser("routes",    help="Install default routes on HostA/HostB")

    mv = sub.add_parser("move", help="Shift traffic north or south path")
    mv.add_argument("direction", choices=["north","south"],
                    help="north = R1→R2→R3, south = R1→R4→R3")

    args = p.parse_args()

    if args.cmd == "construct":
        construct_network()
    elif args.cmd == "ospf":
        start_ospf()
    elif args.cmd == "routes":
        install_host_routes()
    elif args.cmd == "move":
        move_traffic(args.direction)
    else:
        p.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
