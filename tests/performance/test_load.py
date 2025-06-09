import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict, Any
import json
import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from tests.utils.test_data_generator import TestDataGenerator

class LoadTest:
    def __init__(self, 
                 base_url: str = "http://localhost:8000",
                 api_key: str = "your-api-key-here",
                 output_dir: str = "test_results"):
        """Initialize the load test with configuration."""
        self.base_url = base_url
        self.api_key = api_key
        self.output_dir = output_dir
        self.data_generator = TestDataGenerator()
        os.makedirs(output_dir, exist_ok=True)
        
    async def make_request(self, 
                          session: aiohttp.ClientSession,
                          endpoint: str,
                          method: str = "GET",
                          data: Dict = None) -> Dict[str, Any]:
        """Make a single request and measure its performance."""
        start_time = time.time()
        headers = {"X-API-Key": self.api_key}
        
        try:
            if method == "GET":
                async with session.get(f"{self.base_url}{endpoint}", headers=headers) as response:
                    response_data = await response.json()
                    status = response.status
            elif method == "POST":
                async with session.post(f"{self.base_url}{endpoint}", 
                                      headers=headers,
                                      json=data) as response:
                    response_data = await response.json()
                    status = response.status
                    
            end_time = time.time()
            latency = (end_time - start_time) * 1000  # Convert to milliseconds
            
            return {
                "status": status,
                "latency": latency,
                "success": 200 <= status < 300,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            end_time = time.time()
            return {
                "status": 0,
                "latency": (end_time - start_time) * 1000,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
    async def run_concurrent_requests(self,
                                    endpoint: str,
                                    method: str,
                                    num_requests: int,
                                    concurrency: int,
                                    data: List[Dict] = None) -> List[Dict[str, Any]]:
        """Run multiple requests concurrently."""
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(num_requests):
                request_data = data[i] if data else None
                task = asyncio.create_task(
                    self.make_request(session, endpoint, method, request_data)
                )
                tasks.append(task)
                
                if len(tasks) >= concurrency:
                    await asyncio.gather(*tasks)
                    tasks = []
                    
            if tasks:
                await asyncio.gather(*tasks)
                
    async def run_load_test(self,
                           endpoint: str,
                           method: str,
                           num_requests: int,
                           concurrency: int,
                           data: List[Dict] = None) -> Dict[str, Any]:
        """Run a load test and collect metrics."""
        start_time = time.time()
        results = await self.run_concurrent_requests(
            endpoint, method, num_requests, concurrency, data
        )
        end_time = time.time()
        
        # Calculate metrics
        latencies = [r["latency"] for r in results]
        successes = [r["success"] for r in results]
        
        metrics = {
            "total_requests": num_requests,
            "concurrency": concurrency,
            "total_time": end_time - start_time,
            "requests_per_second": num_requests / (end_time - start_time),
            "success_rate": sum(successes) / len(successes),
            "latency": {
                "min": min(latencies),
                "max": max(latencies),
                "mean": statistics.mean(latencies),
                "median": statistics.median(latencies),
                "p95": sorted(latencies)[int(len(latencies) * 0.95)],
                "p99": sorted(latencies)[int(len(latencies) * 0.99)]
            }
        }
        
        return metrics
        
    def save_results(self, 
                    metrics: Dict[str, Any],
                    test_name: str):
        """Save test results to files."""
        # Save metrics
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metrics_file = os.path.join(self.output_dir, f"{test_name}_{timestamp}_metrics.json")
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
            
        # Generate and save plots
        self.generate_plots(metrics, test_name, timestamp)
        
    def generate_plots(self,
                      metrics: Dict[str, Any],
                      test_name: str,
                      timestamp: str):
        """Generate performance plots."""
        # Latency distribution
        plt.figure(figsize=(10, 6))
        plt.hist(metrics["latency"]["values"], bins=50)
        plt.title("Latency Distribution")
        plt.xlabel("Latency (ms)")
        plt.ylabel("Frequency")
        plt.savefig(os.path.join(self.output_dir, f"{test_name}_{timestamp}_latency_dist.png"))
        plt.close()
        
        # Throughput over time
        plt.figure(figsize=(10, 6))
        plt.plot(metrics["throughput_over_time"])
        plt.title("Throughput Over Time")
        plt.xlabel("Time (s)")
        plt.ylabel("Requests per second")
        plt.savefig(os.path.join(self.output_dir, f"{test_name}_{timestamp}_throughput.png"))
        plt.close()
        
    async def run_test_suite(self):
        """Run a complete test suite."""
        # Test 1: Basic load test
        print("Running basic load test...")
        metrics = await self.run_load_test(
            endpoint="/predict",
            method="POST",
            num_requests=1000,
            concurrency=50,
            data=self.data_generator.generate_performance_test_data(1000)
        )
        self.save_results(metrics, "basic_load")
        
        # Test 2: High concurrency test
        print("Running high concurrency test...")
        metrics = await self.run_load_test(
            endpoint="/predict",
            method="POST",
            num_requests=5000,
            concurrency=200,
            data=self.data_generator.generate_performance_test_data(5000)
        )
        self.save_results(metrics, "high_concurrency")
        
        # Test 3: Endurance test
        print("Running endurance test...")
        metrics = await self.run_load_test(
            endpoint="/predict",
            method="POST",
            num_requests=10000,
            concurrency=100,
            data=self.data_generator.generate_performance_test_data(10000)
        )
        self.save_results(metrics, "endurance")
        
        # Test 4: Mixed workload test
        print("Running mixed workload test...")
        endpoints = ["/predict", "/health", "/metrics"]
        methods = ["POST", "GET", "GET"]
        num_requests = 3000
        concurrency = 100
        
        all_metrics = []
        for endpoint, method in zip(endpoints, methods):
            metrics = await self.run_load_test(
                endpoint=endpoint,
                method=method,
                num_requests=num_requests,
                concurrency=concurrency
            )
            all_metrics.append(metrics)
            
        combined_metrics = {
            "endpoints": endpoints,
            "metrics": all_metrics
        }
        self.save_results(combined_metrics, "mixed_workload")
        
if __name__ == "__main__":
    # Run the test suite
    load_test = LoadTest()
    asyncio.run(load_test.run_test_suite()) 