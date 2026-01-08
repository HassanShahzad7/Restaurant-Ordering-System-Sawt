-- Initialize test database
CREATE DATABASE IF NOT EXISTS sawt_test;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE sawt TO sawt;
GRANT ALL PRIVILEGES ON DATABASE sawt_test TO sawt;
