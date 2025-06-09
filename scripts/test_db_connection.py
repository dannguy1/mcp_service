import os
import sys
import asyncio
import asyncpg
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_connection():
    """Test database connection and basic operations."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get database configuration
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            logger.error("DATABASE_URL not found in environment variables")
            return False

        logger.info("Attempting to connect to database...")
        
        # Test connection
        conn = await asyncpg.connect(db_url)
        logger.info("Successfully connected to database!")

        # Test basic query
        version = await conn.fetchval('SELECT version();')
        logger.info(f"PostgreSQL version: {version}")

        # Test table existence
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        logger.info("\nAvailable tables:")
        for table in tables:
            logger.info(f"- {table['table_name']}")

        # Test log_entries table structure
        try:
            columns = await conn.fetch("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'log_entries'
            """)
            
            logger.info("\nlog_entries table structure:")
            for col in columns:
                logger.info(f"- {col['column_name']}: {col['data_type']}")
        except Exception as e:
            logger.warning(f"Could not fetch log_entries structure: {e}")

        # Test sample data
        try:
            count = await conn.fetchval("SELECT COUNT(*) FROM log_entries")
            logger.info(f"\nTotal log entries: {count}")
            
            if count > 0:
                sample = await conn.fetchrow("""
                    SELECT * FROM log_entries 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """)
                logger.info("\nMost recent log entry:")
                for key, value in sample.items():
                    logger.info(f"- {key}: {value}")
        except Exception as e:
            logger.warning(f"Could not fetch sample data: {e}")

        await conn.close()
        logger.info("\nDatabase connection test completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

if __name__ == "__main__":
    try:
        asyncio.run(test_connection())
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1) 