#!/usr/bin/env python3
import os
import sys
import pytest
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_tests():
    """Run all tests in the project."""
    start_time = datetime.now()
    logger.info("Starting test execution...")
    
    # Get the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Add project root to Python path
    sys.path.insert(0, project_root)
    
    # Configure pytest arguments
    pytest_args = [
        'tests',  # Test directory
        '-v',     # Verbose output
        '--tb=short',  # Shorter traceback format
        '--cov=components',  # Enable coverage for components
        '--cov=agents',      # Enable coverage for agents
        '--cov-report=term-missing',  # Show missing lines in coverage report
        '--cov-report=html:coverage_report',  # Generate HTML coverage report
        '-p', 'no:warnings',  # Disable warning capture
    ]
    
    try:
        # Run tests
        exit_code = pytest.main(pytest_args)
        
        # Calculate and log execution time
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"Test execution completed in {duration}")
        
        if exit_code == 0:
            logger.info("All tests passed successfully!")
        else:
            logger.error(f"Tests failed with exit code: {exit_code}")
        
        return exit_code
        
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(run_tests()) 