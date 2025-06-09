import asyncio
import argparse
import sys
import os
from datetime import datetime
from typing import List, Dict, Any
import json

from tests.performance.test_load import LoadTest
from tests.security.test_api_security import APISecurityTest
from tests.utils.test_data_generator import TestDataGenerator

class TestRunner:
    def __init__(self, 
                 base_url: str = "http://localhost:8000",
                 output_dir: str = "test_results"):
        """Initialize the test runner.
        
        Args:
            base_url: URL of the model server to test (e.g., http://localhost:8000)
            output_dir: Directory to save test results
        """
        self.base_url = base_url
        self.output_dir = output_dir
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_dir = os.path.join(output_dir, self.timestamp)
        os.makedirs(self.results_dir, exist_ok=True)
        
    async def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance test suite."""
        print("\nRunning Performance Tests...")
        load_test = LoadTest(base_url=self.base_url,
                           output_dir=os.path.join(self.results_dir, "performance"))
        await load_test.run_test_suite()
        return {"status": "completed"}
        
    async def run_security_tests(self) -> Dict[str, Any]:
        """Run security test suite."""
        print("\nRunning Security Tests...")
        security_test = APISecurityTest(base_url=self.base_url,
                                      output_dir=os.path.join(self.results_dir, "security"))
        await security_test.run_security_suite()
        return {"status": "completed"}
        
    def save_test_results(self, results: Dict[str, Any]):
        """Save test results to a JSON file."""
        results_file = os.path.join(self.results_dir, "test_results.json")
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
            
    async def run_all_tests(self):
        """Run all test suites and save results."""
        results = {
            "timestamp": self.timestamp,
            "base_url": self.base_url,
            "suites": {}
        }
        
        try:
            # Run performance tests
            results["suites"]["performance"] = await self.run_performance_tests()
            
            # Run security tests
            results["suites"]["security"] = await self.run_security_tests()
            
            # Save results
            self.save_test_results(results)
            
            print(f"\nAll tests completed successfully!")
            print(f"Results saved to: {self.results_dir}")
            
        except Exception as e:
            print(f"Error running tests: {str(e)}")
            sys.exit(1)
            
def main():
    parser = argparse.ArgumentParser(
        description="Run test suites for the WiFi Anomaly Detection Model Server"
    )
    parser.add_argument(
        "--base-url", 
        default="http://localhost:8000",
        help="URL of the model server to test (e.g., http://localhost:8000 or http://192.168.10.8:8000)"
    )
    parser.add_argument(
        "--output-dir",
        default="test_results",
        help="Directory to save test results"
    )
    
    args = parser.parse_args()
    
    # Validate base URL
    if not args.base_url.startswith(("http://", "https://")):
        print("Error: base-url must start with http:// or https://")
        sys.exit(1)
        
    print(f"Testing model server at: {args.base_url}")
    print(f"Results will be saved to: {args.output_dir}")
    
    runner = TestRunner(base_url=args.base_url,
                       output_dir=args.output_dir)
    
    asyncio.run(runner.run_all_tests())
    
if __name__ == "__main__":
    main() 