#!/usr/bin/env python3
import os
import sys
import pytest
import coverage
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_tests():
    """Run all tests with coverage reporting."""
    # Start coverage
    cov = coverage.Coverage(
        branch=True,
        source=['agents', 'components', 'models'],
        omit=[
            '*/tests/*',
            '*/__init__.py',
            '*/conftest.py'
        ]
    )
    cov.start()
    
    # Run tests
    test_args = [
        'tests/unit',
        'tests/integration',
        '-v',
        '--cov',
        '--cov-report=term-missing',
        '--cov-report=html',
        '--cov-report=xml',
        '--junitxml=test-results.xml'
    ]
    
    # Add any command line arguments
    test_args.extend(sys.argv[1:])
    
    # Run pytest
    result = pytest.main(test_args)
    
    # Stop coverage and save report
    cov.stop()
    cov.save()
    
    # Generate coverage reports
    cov.html_report(directory='coverage_html')
    cov.xml_report(outfile='coverage.xml')
    
    return result

if __name__ == '__main__':
    sys.exit(run_tests()) 