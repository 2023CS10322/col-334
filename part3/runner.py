#!/usr/bin/env python3

import json
import os
import time
import glob
import numpy as np

class Runner:
    def __init__(self, config_file='config.json'):
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.server_ip = self.config['server_ip']
        self.port = self.config['port']
        self.num_clients = self.config['num_clients']
        self.c = self.config['c']  # Batch size for rogue client
        self.p = self.config['p']  # Offset (always 0) since we want to download the full file
        self.k = self.config['k']  # Words per request (always 5)
        
        print(f"Config: {self.num_clients} clients, c={self.c}, p={self.p}, k={self.k}")
    
    def cleanup_logs(self):
        """Clean old log files"""
        logs = glob.glob("logs/*.log")
        for log in logs:
            os.remove(log)
        print("Cleaned old logs")
    
    def parse_logs(self):
        """
        TODO:
        Parse log files and return completion times
        Return: {'rogue': [times], 'normal': [times]}
        """
        print("TODO: Implement parse_logs() function")
        return {'rogue': [], 'normal': []}
    
    def calculate_jfi(self, completion_times):
        """
        TODO:
        Calculate Jain's Fairness Index
        Note: JFI runs under the - more is better policy; 
        i.e., JFI's variable must represent a positive benefit measure (e.g., throughput, share of CPU, utility).
        
        Formula: JFI = (sum of utilities)^2 / (n * sum of utilities^2)
        
        """
        pass
    
    def run_experiment(self, c_value):
        """Run single experiment with given c value"""
        print(f"Running experiment with c={c_value}")
        
        # Clean logs
        self.cleanup_logs()
        
        # Create network
        from topology import create_network
        net = create_network(num_clients=self.num_clients)
        
        try:
            # Get hosts
            server = net.get('server')
            clients = [net.get(f'client{i+1}') for i in range(self.num_clients)]
            
            # Start server (students create server.py)
            print("Starting server...")
            server_proc = server.popen("python3 server.py")
            time.sleep(3)
            
            # Start clients
            print("Starting clients...")
            # Client 1 is rogue (batch size c)
            rogue_proc = clients[0].popen(f"python3 client.py --batch-size {c_value} --client-id rogue")
            
            # Clients 2-N are normal (batch size 1)
            normal_procs = []
            for i in range(1, self.num_clients):
                proc = clients[i].popen(f"python3 client.py --batch-size 1 --client-id normal_{i+1}")
                normal_procs.append(proc)
            
            # Wait for all clients
            rogue_proc.wait()
            for proc in normal_procs:
                proc.wait()
            
            # Stop server
            server_proc.terminate()
            server_proc.wait()
            time.sleep(2)
            
            # Parse results
            time.sleep(1)
            results = self.parse_logs()
            
            return results
            
        finally:
            net.stop()
    
    def run_varying_c(self):
        """Run experiments with c starting from config value, incrementing by 2 until <= 20"""
        c_values = list(range(self.c, 21, 2)) 
        
        print("Running experiments with varying c values...")
        
        for c in c_values:
            print(f"\n--- Testing c = {c} ---")
            results = self.run_experiment(c)
            
            # TODO: Students implement result saving/logging
            # TODO: Students implement metrics calculation and JFI
            print(f"Experiment with c={c} completed")
        
        print("All experiments completed")
        # TODO: Students implement result analysis and plotting

    def plot_jfi_vs_c(self, results):
        """
        TODO: 
        Plot JFI values vs c values
        """
        pass

def main():
    runner = Runner()
    
    # Run experiments with varying c values
    runner.run_varying_c()
    
    # TODO: Students implement result saving and analysis

if __name__ == '__main__':
    main()