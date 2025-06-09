# Troubleshooting Guide

This guide covers common issues you might encounter while running the WiFi Anomaly Detection Model Server and their solutions.

## Server Issues

### Server Won't Start

**Symptoms:**
- Server fails to start
- Error messages in logs
- Port already in use

**Solutions:**
1. Check if the port is already in use:
   ```bash
   sudo lsof -i :8000
   ```
2. Verify all required services are running:
   ```bash
   docker-compose ps
   ```
3. Check server logs:
   ```bash
   docker-compose logs model_server
   ```

### High Memory Usage

**Symptoms:**
- Slow response times
- High memory usage in monitoring
- Out of memory errors

**Solutions:**
1. Adjust batch size in `config/server_config.yaml`:
   ```yaml
   model:
     batch_size: 16  # Reduce from default
   ```
2. Clear model cache:
   ```bash
   curl -X POST http://localhost:8000/models/clear-cache
   ```
3. Check for memory leaks in logs

## Model Issues

### Poor Prediction Performance

**Symptoms:**
- High anomaly detection rate
- Low accuracy metrics
- Model drift alerts

**Solutions:**
1. Check model drift metrics:
   ```bash
   curl http://localhost:8000/metrics | grep drift
   ```
2. Retrain model with recent data:
   ```bash
   curl -X POST http://localhost:8000/train
   ```
3. Compare model versions:
   ```bash
   curl http://localhost:8000/models/compare/v1/v2
   ```

### Model Loading Failures

**Symptoms:**
- 500 errors on prediction endpoints
- Model not found errors
- Version mismatch errors

**Solutions:**
1. Verify model files exist:
   ```bash
   ls -l models/versions/
   ```
2. Check model metadata:
   ```bash
   curl http://localhost:8000/models/versions/latest
   ```
3. Reload model:
   ```bash
   curl -X POST http://localhost:8000/models/reload
   ```

## Database Issues

### Connection Problems

**Symptoms:**
- Database connection errors
- Slow queries
- Connection pool exhaustion

**Solutions:**
1. Check database connection:
   ```bash
   docker-compose exec postgres pg_isready
   ```
2. Verify credentials in `.env`
3. Check connection pool settings in `config/server_config.yaml`

### Data Quality Issues

**Symptoms:**
- Data quality alerts
- Missing or invalid data
- Inconsistent predictions

**Solutions:**
1. Check data quality metrics:
   ```bash
   curl http://localhost:8000/metrics | grep quality
   ```
2. Verify data pipeline:
   ```bash
   curl http://localhost:8000/health
   ```
3. Check data validation rules

## Monitoring Issues

### Prometheus Metrics Not Showing

**Symptoms:**
- Empty metrics endpoint
- Missing graphs in Grafana
- No alerts

**Solutions:**
1. Check Prometheus configuration:
   ```bash
   docker-compose exec prometheus promtool check config /etc/prometheus/prometheus.yml
   ```
2. Verify metrics endpoint:
   ```bash
   curl http://localhost:8000/metrics
   ```
3. Check Prometheus targets:
   ```bash
   curl http://localhost:9090/api/v1/targets
   ```

### Grafana Dashboard Issues

**Symptoms:**
- Missing panels
- No data in graphs
- Dashboard errors

**Solutions:**
1. Check Grafana logs:
   ```bash
   docker-compose logs grafana
   ```
2. Verify data source connection
3. Check dashboard JSON:
   ```bash
   cat monitoring/grafana_dashboard.json
   ```

## Security Issues

### Authentication Failures

**Symptoms:**
- 401 Unauthorized errors
- Invalid API key errors
- Token expiration issues

**Solutions:**
1. Verify API key:
   ```bash
   echo $API_KEY
   ```
2. Check token expiration:
   ```bash
   curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/health
   ```
3. Reset API key if needed

### Rate Limiting Issues

**Symptoms:**
- 429 Too Many Requests errors
- Slow response times
- Rate limit alerts

**Solutions:**
1. Check rate limit settings:
   ```bash
   echo $RATE_LIMIT
   ```
2. Monitor request rates:
   ```bash
   curl http://localhost:8000/metrics | grep rate_limit
   ```
3. Adjust rate limits if needed

## Performance Tuning

### Slow Response Times

**Symptoms:**
- High latency metrics
- Slow predictions
- Resource exhaustion

**Solutions:**
1. Check resource usage:
   ```bash
   docker stats
   ```
2. Adjust worker count:
   ```yaml
   server:
     workers: 4  # Adjust based on CPU cores
   ```
3. Enable caching:
   ```yaml
   model:
     cache_size: 1000
   ```

### Resource Optimization

**Symptoms:**
- High CPU usage
- Memory pressure
- Disk I/O bottlenecks

**Solutions:**
1. Optimize batch processing:
   ```yaml
   model:
     batch_size: 32
     processing_interval: 300
   ```
2. Enable model quantization
3. Use model caching

## Getting Help

If you're still experiencing issues:

1. Check the logs:
   ```bash
   docker-compose logs -f
   ```

2. Review the documentation:
   - [Deployment Guide](deployment.md)
   - [API Documentation](api.md)
   - [Monitoring Guide](monitoring.md)

3. Contact support:
   - Create an issue on GitHub
   - Email: support@example.com
   - Slack: #model-server-support 