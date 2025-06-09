#!/usr/bin/env python3
import os
import sys
import logging
import yaml
import subprocess
from pathlib import Path
from typing import Dict, List

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import Config
from utils.logger import setup_logger

class MonitoringSetup:
    def __init__(self, config_path: str = "config/monitoring_config.yaml"):
        self.config = Config()
        self.logger = setup_logger("monitoring_setup")
        self.monitoring_config = self._load_monitoring_config(config_path)
        self.prometheus_dir = Path("monitoring/prometheus")
        self.grafana_dir = Path("monitoring/grafana")
        self.setup_directories()

    def _load_monitoring_config(self, config_path: str) -> Dict:
        """Load monitoring configuration."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Failed to load monitoring config: {e}")
            return {}

    def setup_directories(self) -> None:
        """Create necessary directories for monitoring."""
        try:
            self.prometheus_dir.mkdir(parents=True, exist_ok=True)
            self.grafana_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info("Created monitoring directories")
        except Exception as e:
            self.logger.error(f"Failed to create directories: {e}")
            raise

    def setup_prometheus(self) -> None:
        """Set up Prometheus configuration."""
        try:
            # Create prometheus.yml
            prometheus_config = {
                "global": {
                    "scrape_interval": "15s",
                    "evaluation_interval": "15s"
                },
                "rule_files": [
                    "rules/*.yml"
                ],
                "scrape_configs": [
                    {
                        "job_name": "mcp_service",
                        "static_configs": [
                            {
                                "targets": ["localhost:8000"]
                            }
                        ]
                    }
                ]
            }
            
            with open(self.prometheus_dir / "prometheus.yml", 'w') as f:
                yaml.dump(prometheus_config, f)
            
            # Create rules directory
            rules_dir = self.prometheus_dir / "rules"
            rules_dir.mkdir(exist_ok=True)
            
            # Create alert rules
            alert_rules = {
                "groups": [
                    {
                        "name": "mcp_service",
                        "rules": [
                            {
                                "alert": rule["name"],
                                "expr": rule["condition"],
                                "for": rule["duration"],
                                "labels": {
                                    "severity": rule["severity"]
                                },
                                "annotations": {
                                    "description": rule["description"]
                                }
                            }
                            for rule in self.monitoring_config.get("prometheus", {}).get("alerting", {}).get("rules", [])
                        ]
                    }
                ]
            }
            
            with open(rules_dir / "alerts.yml", 'w') as f:
                yaml.dump(alert_rules, f)
            
            self.logger.info("Prometheus configuration created")
        except Exception as e:
            self.logger.error(f"Failed to set up Prometheus: {e}")
            raise

    def setup_grafana(self) -> None:
        """Set up Grafana configuration."""
        try:
            # Create datasources directory
            datasources_dir = self.grafana_dir / "datasources"
            datasources_dir.mkdir(exist_ok=True)
            
            # Create Prometheus datasource
            prometheus_datasource = {
                "apiVersion": 1,
                "datasources": [
                    {
                        "name": "Prometheus",
                        "type": "prometheus",
                        "access": "proxy",
                        "url": "http://prometheus:9090",
                        "isDefault": True
                    }
                ]
            }
            
            with open(datasources_dir / "prometheus.yml", 'w') as f:
                yaml.dump(prometheus_datasource, f)
            
            # Create dashboards directory
            dashboards_dir = self.grafana_dir / "dashboards"
            dashboards_dir.mkdir(exist_ok=True)
            
            # Create dashboard configurations
            for dashboard_name, dashboard_config in self.monitoring_config.get("grafana", {}).get("dashboards", {}).items():
                dashboard = {
                    "apiVersion": 1,
                    "providers": [
                        {
                            "name": dashboard_name,
                            "orgId": 1,
                            "folder": "",
                            "type": "file",
                            "disableDeletion": False,
                            "editable": True,
                            "options": {
                                "path": f"/etc/grafana/provisioning/dashboards/{dashboard_name}"
                            }
                        }
                    ]
                }
                
                with open(dashboards_dir / f"{dashboard_name}.yml", 'w') as f:
                    yaml.dump(dashboard, f)
                
                # Create dashboard JSON
                dashboard_json = {
                    "annotations": {
                        "list": []
                    },
                    "editable": True,
                    "fiscalYearStartMonth": 0,
                    "graphTooltip": 0,
                    "links": [],
                    "liveNow": False,
                    "panels": [],
                    "refresh": "5s",
                    "schemaVersion": 38,
                    "style": "dark",
                    "tags": [],
                    "templating": {
                        "list": []
                    },
                    "time": {
                        "from": "now-6h",
                        "to": "now"
                    },
                    "timepicker": {},
                    "timezone": "",
                    "title": dashboard_config["title"],
                    "uid": f"{dashboard_name.lower().replace(' ', '_')}",
                    "version": 1,
                    "weekStart": ""
                }
                
                # Add panels
                for panel in dashboard_config.get("panels", []):
                    panel_json = {
                        "title": panel["title"],
                        "type": panel["type"],
                        "datasource": {
                            "type": "prometheus",
                            "uid": "prometheus"
                        },
                        "targets": [
                            {
                                "expr": metric,
                                "refId": f"metric_{i}"
                            }
                            for i, metric in enumerate(panel["metrics"])
                        ]
                    }
                    dashboard_json["panels"].append(panel_json)
                
                with open(dashboards_dir / f"{dashboard_name}.json", 'w') as f:
                    yaml.dump(dashboard_json, f)
            
            self.logger.info("Grafana configuration created")
        except Exception as e:
            self.logger.error(f"Failed to set up Grafana: {e}")
            raise

    def setup_monitoring(self) -> None:
        """Set up complete monitoring environment."""
        try:
            self.logger.info("Starting monitoring setup")
            
            # Set up Prometheus
            self.setup_prometheus()
            self.logger.info("Prometheus setup completed")
            
            # Set up Grafana
            self.setup_grafana()
            self.logger.info("Grafana setup completed")
            
            self.logger.info("Monitoring setup completed successfully")
        except Exception as e:
            self.logger.error(f"Monitoring setup failed: {e}")
            raise

def main():
    """Main entry point."""
    try:
        setup = MonitoringSetup()
        setup.setup_monitoring()
    except Exception as e:
        logging.error(f"Monitoring setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 