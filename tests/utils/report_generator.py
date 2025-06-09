import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Dict, Any, List
import jinja2
import yaml

class TestReportGenerator:
    def __init__(self, results_dir: str, config_path: str):
        """Initialize the test report generator."""
        self.results_dir = results_dir
        self.config = self._load_config(config_path)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load test configuration."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
            
    def _load_test_results(self) -> Dict[str, Any]:
        """Load test results from JSON file."""
        results_file = os.path.join(self.results_dir, "test_results.json")
        with open(results_file, 'r') as f:
            return json.load(f)
            
    def generate_performance_plots(self, results: Dict[str, Any]):
        """Generate performance test plots."""
        performance_dir = os.path.join(self.results_dir, "performance")
        os.makedirs(performance_dir, exist_ok=True)
        
        # Load performance metrics
        metrics_file = os.path.join(performance_dir, "metrics.json")
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
            
        # Plot latency distribution
        plt.figure(figsize=(10, 6))
        plt.hist(metrics["latency_ms"], bins=50)
        plt.title("Latency Distribution")
        plt.xlabel("Latency (ms)")
        plt.ylabel("Frequency")
        plt.savefig(os.path.join(performance_dir, "latency_distribution.png"))
        plt.close()
        
        # Plot throughput over time
        plt.figure(figsize=(10, 6))
        plt.plot(metrics["timestamps"], metrics["throughput"])
        plt.title("Throughput Over Time")
        plt.xlabel("Time")
        plt.ylabel("Requests per Second")
        plt.savefig(os.path.join(performance_dir, "throughput.png"))
        plt.close()
        
    def generate_html_report(self, results: Dict[str, Any]):
        """Generate HTML test report."""
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))
        template = env.get_template("report_template.html")
        
        # Prepare report data
        report_data = {
            "timestamp": self.timestamp,
            "test_environment": self.config["test_environment"],
            "results": results,
            "metrics": self.config["metrics"],
            "performance_plots": [
                "latency_distribution.png",
                "throughput.png"
            ]
        }
        
        # Render report
        html_report = template.render(**report_data)
        
        # Save report
        report_file = os.path.join(self.results_dir, "test_report.html")
        with open(report_file, 'w') as f:
            f.write(html_report)
            
    def generate_csv_report(self, results: Dict[str, Any]):
        """Generate CSV test report."""
        # Convert results to DataFrame
        df = pd.DataFrame(results["suites"])
        
        # Save to CSV
        csv_file = os.path.join(self.results_dir, "test_results.csv")
        df.to_csv(csv_file, index=False)
        
    def generate_reports(self):
        """Generate all test reports."""
        print("Generating test reports...")
        
        # Load test results
        results = self._load_test_results()
        
        # Generate performance plots
        self.generate_performance_plots(results)
        
        # Generate HTML report
        self.generate_html_report(results)
        
        # Generate CSV report
        self.generate_csv_report(results)
        
        print(f"Reports generated in: {self.results_dir}")
        
if __name__ == "__main__":
    # Example usage
    generator = TestReportGenerator(
        results_dir="test_results/20240315_123456",
        config_path="tests/config/test_config.yaml"
    )
    generator.generate_reports() 