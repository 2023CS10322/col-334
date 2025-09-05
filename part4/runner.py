#!/usr/bin/env python3

import json
import os
import time
import glob
import numpy as np
import argparse
import matplotlib.pyplot as plt

class Runner:
    def __init__(self, config_file='config.json'):
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.server_ip = self.config['server_ip']
        self.port = self.config['port']
        self.num_clients = self.config['num_clients']
        self.c = self.config['c']
        self.p = self.config['p']
        self.k = self.config['k']
        self.num_repetitions = self.config.get('num_repetitions', 2)
        
        print(f"Config: {self.num_clients} clients, c={self.c}, p={self.p}, k={self.k}")
    
    def cleanup_logs(self):
        """Clean old log files"""
        logs = glob.glob("logs/*.log")
        for log in logs:
            os.remove(log)
        print("Cleaned old logs")
    
    def parse_logs(self):
        """Parse log files and return completion times"""
        completion_times = {'rogue': [], 'normal': []}
        
        log_files = glob.glob("logs/*.log")
        for log_file in log_files:
            with open(log_file, 'r') as f:
                try:
                    time_val = float(f.read().strip())
                    if 'rogue' in log_file:
                        completion_times['rogue'].append(time_val)
                    else:
                        completion_times['normal'].append(time_val)
                except ValueError:
                    print(f"Invalid content in {log_file}")
        
        return completion_times
    
    def calculate_jfi(self, completion_times):
        """Calculate Jain's Fairness Index"""
        # Convert completion times to throughput (benefit metric)
        throughputs = [1/t for t in completion_times]
        
        n = len(throughputs)
        if n == 0:
            return 0
            
        sum_throughput = sum(throughputs)
        sum_squared_throughput = sum(t**2 for t in throughputs)
        
        jfi = (sum_throughput ** 2) / (n * sum_squared_throughput)
        return jfi
    
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
            
            # Start server
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
        """Run experiments with c from 1 to 10"""
        c_values = list(range(1, 50,4))
        jfi_results = []
        
        print("Running experiments with varying c values...")
        
        for c in c_values:
            jfi_sum = 0
            for rep in range(self.num_repetitions):
                print(f"\n--- Testing c = {c}, repetition {rep+1}/{self.num_repetitions} ---")
                results = self.run_experiment(c)
                
                # Combine all completion times
                all_times = results['rogue'] + results['normal']
                jfi = self.calculate_jfi(all_times)
                jfi_sum += jfi
                
                print(f"JFI for c={c}, rep{rep+1}: {jfi:.4f}")
            
            avg_jfi = jfi_sum / self.num_repetitions
            jfi_results.append(avg_jfi)
            print(f"Average JFI for c={c}: {avg_jfi:.4f}")
            
            # Save results to CSV
            with open('results.csv', 'a') as f:
                f.write(f"{c},{avg_jfi:.4f}\n")
        
        return c_values, jfi_results
    
    def plot_jfi_vs_c(self, c_values, jfi_values):
        """Plot JFI values vs c values"""
        plt.figure(figsize=(8, 6))
        plt.plot(c_values, jfi_values, 'o-', linewidth=2, markersize=8)
        plt.xlabel('Number of parallel requests (c)')
        plt.ylabel("Jain's Fairness Index (JFI)")
        plt.title('Fairness vs Greediness (FCFS Scheduling)')
        plt.grid(True, alpha=0.3)
        plt.ylim(0, 1.1)
        plt.savefig('p3_plot.png', dpi=300, bbox_inches='tight')
        plt.show()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--single', action='store_true', help='Run single experiment with config c value')
    args = parser.parse_args()
    
    runner = Runner()
    
    if args.single:
        # Run single experiment with config c value
        results = runner.run_experiment(runner.c)
        all_times = results['rogue'] + results['normal']
        jfi = runner.calculate_jfi(all_times)
        print(f"JFI for c={runner.c}: {jfi:.4f}")
    else:
        # Run experiments with varying c values
        if os.path.exists('results.csv'):
            os.remove('results.csv')
            
        c_values, jfi_results = runner.run_varying_c()
        runner.plot_jfi_vs_c(c_values, jfi_results)

if __name__ == '__main__':
    main()