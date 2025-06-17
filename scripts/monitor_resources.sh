#!/bin/bash

# Resource monitoring script for low-performance devices

LOG_FILE="./logs/resource_monitor.log"
ALERT_THRESHOLD_CPU=80
ALERT_THRESHOLD_MEMORY=85
ALERT_THRESHOLD_DISK=90

# Create logs directory if it doesn't exist
mkdir -p ./logs

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

check_resources() {
    # Check CPU usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
    
    # Check memory usage
    memory_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    
    # Check disk usage
    disk_usage=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
    
    # Check process counts
    mcp_processes=$(pgrep -f "mcp_service.py" | wc -l)
    backend_processes=$(pgrep -f "uvicorn.*app.main:app" | wc -l)
    redis_processes=$(pgrep -f "redis-server" | wc -l)
    
    # Log current status
    log_message "CPU: ${cpu_usage}%, Memory: ${memory_usage}%, Disk: ${disk_usage}%"
    log_message "Processes - MCP: $mcp_processes, Backend: $backend_processes, Redis: $redis_processes"
    
    # Check for alerts
    if (( $(echo "$cpu_usage > $ALERT_THRESHOLD_CPU" | bc -l) )); then
        log_message "ALERT: High CPU usage: ${cpu_usage}%"
    fi
    
    if (( $(echo "$memory_usage > $ALERT_THRESHOLD_MEMORY" | bc -l) )); then
        log_message "ALERT: High memory usage: ${memory_usage}%"
    fi
    
    if (( $(echo "$disk_usage > $ALERT_THRESHOLD_DISK" | bc -l) )); then
        log_message "ALERT: High disk usage: ${disk_usage}%"
    fi
    
    # Check if services are running
    if [ "$mcp_processes" -eq 0 ]; then
        log_message "ALERT: MCP service is not running"
    fi
    
    if [ "$backend_processes" -eq 0 ]; then
        log_message "ALERT: Backend service is not running"
    fi
    
    if [ "$redis_processes" -eq 0 ]; then
        log_message "ALERT: Redis is not running"
    fi
}

# Main monitoring loop
main() {
    log_message "Starting resource monitoring..."
    
    while true; do
        check_resources
        sleep 60  # Check every minute
    done
}

main "$@" 