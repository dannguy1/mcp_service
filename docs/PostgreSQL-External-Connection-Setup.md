# PostgreSQL External Connection Setup Guide

## Problem Description

When testing database connections from the Settings page, connections to `localhost` work fine, but connections to external hosts (e.g., `192.168.10.12`) fail with:

```
Error! Connection failed: [Errno 111] Connection refused. Please check the host, port, and ensure the database server is running.
```

This is a PostgreSQL configuration issue where the database server is not configured to accept connections from external hosts.

## Root Cause

PostgreSQL by default only accepts connections from localhost (`127.0.0.1`). To allow external connections, you need to modify:

1. **`postgresql.conf`**: Configure which network interfaces PostgreSQL listens on
2. **`pg_hba.conf`**: Configure which hosts are allowed to connect and how they authenticate

## Solution Steps

### Step 1: Locate PostgreSQL Configuration Files

First, find where PostgreSQL is installed and where its configuration files are located:

```bash
# Find PostgreSQL installation
sudo find /etc -name "postgresql.conf" 2>/dev/null
sudo find /var/lib -name "postgresql.conf" 2>/dev/null

# Common locations:
# Ubuntu/Debian: /etc/postgresql/{version}/main/
# CentOS/RHEL: /var/lib/pgsql/data/
# macOS (Homebrew): /usr/local/var/postgres/
```

### Step 2: Configure `postgresql.conf`

Edit the `postgresql.conf` file to allow external connections:

```bash
# Backup the original file
sudo cp /etc/postgresql/14/main/postgresql.conf /etc/postgresql/14/main/postgresql.conf.backup

# Edit the configuration file
sudo nano /etc/postgresql/14/main/postgresql.conf
```

Find and modify these lines:

```ini
# Listen on all available network interfaces
listen_addresses = '*'

# Port configuration (default is 5432)
port = 5432

# Maximum number of connections
max_connections = 100
```

**Important**: Replace `'*'` with specific IP addresses for better security:
```ini
listen_addresses = 'localhost,192.168.10.12'
```

### Step 3: Configure `pg_hba.conf`

Edit the `pg_hba.conf` file to allow connections from external hosts:

```bash
# Backup the original file
sudo cp /etc/postgresql/14/main/pg_hba.conf /etc/postgresql/14/main/pg_hba.conf.backup

# Edit the configuration file
sudo nano /etc/postgresql/14/main/pg_hba.conf
```

Add or modify these lines to allow connections from your network:

```ini
# TYPE  DATABASE        USER            ADDRESS                 METHOD

# Local connections
local   all             all                                     peer

# IPv4 local connections
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5

# Allow connections from your specific network
host    all             all             192.168.10.0/24         md5

# Allow connections from specific host
host    all             all             192.168.10.12/32        md5

# Allow connections from any host (less secure, use only for testing)
# host    all             all             0.0.0.0/0               md5
```

### Step 4: Restart PostgreSQL Service

After making configuration changes, restart PostgreSQL:

```bash
# Ubuntu/Debian
sudo systemctl restart postgresql

# CentOS/RHEL
sudo systemctl restart postgresql

# macOS
brew services restart postgresql
```

### Step 5: Verify Configuration

Check if PostgreSQL is listening on external interfaces:

```bash
# Check listening ports
sudo netstat -tlnp | grep postgres
# or
sudo ss -tlnp | grep postgres

# Expected output should show:
# tcp        0      0 0.0.0.0:5432           0.0.0.0:*               LISTEN
```

### Step 6: Test Connection

Test the connection from your application:

```bash
# Test with psql
psql -h 192.168.10.12 -p 5432 -U your_username -d your_database

# Test with the improved database connection test
python test_db_connection_improved.py
```

## Security Considerations

### 1. Network Security

- **Firewall Configuration**: Ensure your firewall allows connections on port 5432
- **VPN/Private Network**: Use VPN or private network for external connections
- **SSL/TLS**: Enable SSL for encrypted connections

### 2. Authentication Methods

Choose appropriate authentication methods in `pg_hba.conf`:

- **`md5`**: Password authentication (recommended)
- **`scram-sha-256`**: More secure password authentication
- **`peer`**: Local connections only
- **`trust`**: No password (insecure, avoid for external connections)

### 3. User Permissions

Create specific users with limited permissions:

```sql
-- Create a user for external connections
CREATE USER external_user WITH PASSWORD 'secure_password';

-- Grant specific permissions
GRANT CONNECT ON DATABASE your_database TO external_user;
GRANT USAGE ON SCHEMA public TO external_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO external_user;
```

## Troubleshooting

### Common Issues

1. **Connection Still Refused**
   - Check if PostgreSQL is running: `sudo systemctl status postgresql`
   - Verify firewall settings: `sudo ufw status`
   - Check if port is listening: `sudo netstat -tlnp | grep 5432`

2. **Authentication Failed**
   - Verify user exists: `\du` in psql
   - Check password: `ALTER USER username PASSWORD 'new_password';`
   - Verify `pg_hba.conf` authentication method

3. **Permission Denied**
   - Check file permissions: `ls -la /etc/postgresql/14/main/`
   - Ensure PostgreSQL can read config files
   - Check SELinux (if applicable): `getenforce`

### Debug Commands

```bash
# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log

# Check system logs
sudo journalctl -u postgresql -f

# Test network connectivity
telnet 192.168.10.12 5432

# Check PostgreSQL process
ps aux | grep postgres
```

## Application Integration

### Environment Variables

Update your application's environment variables:

```bash
# .env file
DB_HOST=192.168.10.12
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_username
DB_PASSWORD=your_password
```

### Connection String Format

```python
# Python connection string
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
```

## Testing with the Improved Connection Test

The improved database connection test will now provide better error messages for different types of connection issues:

```bash
# Run the test script
python test_db_connection_improved.py
```

Expected successful output:
```json
{
  "status": "success",
  "message": "Database connection test successful",
  "details": {
    "host": "192.168.10.12",
    "port": 5432,
    "database": "your_database",
    "user": "your_username",
    "test_query_result": 1
  }
}
```

## Summary

To fix the "Connection refused" error for external hosts:

1. **Configure `postgresql.conf`**: Set `listen_addresses = '*'` or specific IPs
2. **Configure `pg_hba.conf`**: Allow connections from your network with `host all all 192.168.10.0/24 md5`
3. **Restart PostgreSQL**: `sudo systemctl restart postgresql`
4. **Verify configuration**: Check if port 5432 is listening on all interfaces
5. **Test connection**: Use the improved database connection test

This will allow your application to successfully test database connections to external PostgreSQL hosts while maintaining security through proper authentication and network configuration. 