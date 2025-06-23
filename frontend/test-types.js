// Simple test to verify types are exported correctly
import { DatabaseConfig, DatabaseTestResult } from './src/services/types.js';

console.log('DatabaseConfig type:', typeof DatabaseConfig);
console.log('DatabaseTestResult type:', typeof DatabaseTestResult);

// Test creating objects with these types
const testConfig = {
  host: 'localhost',
  port: 5432,
  database: 'test_db',
  user: 'test_user',
  password: 'test_password'
};

const testResult = {
  status: 'success',
  message: 'Connection successful',
  details: {
    host: 'localhost',
    port: 5432,
    database: 'test_db',
    user: 'test_user'
  }
};

console.log('Test config:', testConfig);
console.log('Test result:', testResult); 