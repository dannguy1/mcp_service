import pytest
import aiohttp
import asyncio
from typing import List, Dict, Any
import json
import os
from tests.utils.test_data_generator import TestDataGenerator

class APISecurityTest:
    def __init__(self, 
                 base_url: str = "http://localhost:8000",
                 output_dir: str = "test_results/security"):
        """Initialize the API security test suite."""
        self.base_url = base_url
        self.output_dir = output_dir
        self.data_generator = TestDataGenerator()
        os.makedirs(output_dir, exist_ok=True)
        
    async def make_request(self,
                          session: aiohttp.ClientSession,
                          endpoint: str,
                          method: str = "GET",
                          headers: Dict = None,
                          data: Dict = None) -> Dict[str, Any]:
        """Make a request and return the response details."""
        try:
            if method == "GET":
                async with session.get(f"{self.base_url}{endpoint}", headers=headers) as response:
                    response_data = await response.json()
                    return {
                        "status": response.status,
                        "headers": dict(response.headers),
                        "data": response_data
                    }
            elif method == "POST":
                async with session.post(f"{self.base_url}{endpoint}",
                                      headers=headers,
                                      json=data) as response:
                    response_data = await response.json()
                    return {
                        "status": response.status,
                        "headers": dict(response.headers),
                        "data": response_data
                    }
        except Exception as e:
            return {
                "status": 0,
                "error": str(e)
            }
            
    async def test_authentication(self):
        """Test various authentication scenarios."""
        async with aiohttp.ClientSession() as session:
            # Test 1: No API key
            response = await self.make_request(session, "/predict", "POST")
            assert response["status"] == 401, "Should require API key"
            
            # Test 2: Invalid API key
            response = await self.make_request(
                session,
                "/predict",
                "POST",
                headers={"X-API-Key": "invalid_key"}
            )
            assert response["status"] == 401, "Should reject invalid API key"
            
            # Test 3: Valid API key
            response = await self.make_request(
                session,
                "/predict",
                "POST",
                headers={"X-API-Key": "your-api-key-here"},
                data=self.data_generator.generate_wifi_log()
            )
            assert response["status"] == 200, "Should accept valid API key"
            
    async def test_rate_limiting(self):
        """Test rate limiting functionality."""
        async with aiohttp.ClientSession() as session:
            headers = {"X-API-Key": "your-api-key-here"}
            responses = []
            
            # Make requests quickly to trigger rate limit
            for _ in range(150):  # Assuming rate limit is 100 requests per minute
                response = await self.make_request(
                    session,
                    "/predict",
                    "POST",
                    headers=headers,
                    data=self.data_generator.generate_wifi_log()
                )
                responses.append(response)
                
            # Check if rate limit was triggered
            rate_limited = any(r["status"] == 429 for r in responses)
            assert rate_limited, "Rate limiting should be enforced"
            
    async def test_input_validation(self):
        """Test input validation and sanitization."""
        async with aiohttp.ClientSession() as session:
            headers = {"X-API-Key": "your-api-key-here"}
            test_cases = self.data_generator.generate_security_test_data()
            
            # Test malicious inputs
            for malicious_input in test_cases["malicious_inputs"]:
                response = await self.make_request(
                    session,
                    "/predict",
                    "POST",
                    headers=headers,
                    data={"input": malicious_input}
                )
                assert response["status"] in [400, 422], "Should reject malicious input"
                
    async def test_cors(self):
        """Test CORS configuration."""
        async with aiohttp.ClientSession() as session:
            # Test with different origins
            origins = [
                "http://localhost:3000",
                "http://malicious-site.com",
                "https://trusted-site.com"
            ]
            
            for origin in origins:
                headers = {
                    "X-API-Key": "your-api-key-here",
                    "Origin": origin
                }
                response = await self.make_request(
                    session,
                    "/predict",
                    "POST",
                    headers=headers,
                    data=self.data_generator.generate_wifi_log()
                )
                
                if origin == "http://localhost:3000":
                    assert "Access-Control-Allow-Origin" in response["headers"], "Should allow trusted origin"
                else:
                    assert "Access-Control-Allow-Origin" not in response["headers"], "Should not allow untrusted origin"
                    
    async def test_sql_injection(self):
        """Test SQL injection prevention."""
        async with aiohttp.ClientSession() as session:
            headers = {"X-API-Key": "your-api-key-here"}
            sql_injection_attempts = [
                "' OR '1'='1",
                "; DROP TABLE users;",
                "' UNION SELECT * FROM users;"
            ]
            
            for attempt in sql_injection_attempts:
                response = await self.make_request(
                    session,
                    "/predict",
                    "POST",
                    headers=headers,
                    data={"query": attempt}
                )
                assert response["status"] in [400, 422], "Should prevent SQL injection"
                
    async def test_xss(self):
        """Test XSS prevention."""
        async with aiohttp.ClientSession() as session:
            headers = {"X-API-Key": "your-api-key-here"}
            xss_attempts = [
                "<script>alert('xss')</script>",
                "javascript:alert('xss')",
                "<img src=x onerror=alert('xss')>"
            ]
            
            for attempt in xss_attempts:
                response = await self.make_request(
                    session,
                    "/predict",
                    "POST",
                    headers=headers,
                    data={"input": attempt}
                )
                assert response["status"] in [400, 422], "Should prevent XSS"
                
    async def run_security_suite(self):
        """Run the complete security test suite."""
        print("Running authentication tests...")
        await self.test_authentication()
        
        print("Running rate limiting tests...")
        await self.test_rate_limiting()
        
        print("Running input validation tests...")
        await self.test_input_validation()
        
        print("Running CORS tests...")
        await self.test_cors()
        
        print("Running SQL injection tests...")
        await self.test_sql_injection()
        
        print("Running XSS tests...")
        await self.test_xss()
        
        print("Security test suite completed successfully!")
        
if __name__ == "__main__":
    # Run the security test suite
    security_test = APISecurityTest()
    asyncio.run(security_test.run_security_suite()) 