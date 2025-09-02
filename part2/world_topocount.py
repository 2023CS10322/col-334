#!/usr/bin/env python3
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSController
import re

def load_config(filename="config.json"):
    config = {}
    with open(filename) as f:
        for line in f:
            line = line.strip().strip(",")
            if not line or line[0] in "{}":
                continue
            key, val = line.split(":", 1)
            key = key.strip().strip('"')
            val = val.strip().strip('"')
            config[key] = val
    return config

class WordcountTopo(Topo):
    def build(self, num_clients=1):
        switch = self.addSwitch("s1")

        # Add server
        server = self.addHost("hS", ip="10.0.0.2")
        self.addLink(server, switch)

        # Add requested number of clients
        for i in range(1, num_clients + 1):
            client = self.addHost(f"h{i}", ip=f"10.0.0.{i+2}")
            self.addLink(client, switch)

def make_net():
    config = load_config("config.json")
    num_clients = int(config.get("num_clients", 1))
    topo = WordcountTopo(num_clients=num_clients)
    net = Mininet(topo=topo, controller=OVSController)
    return net
