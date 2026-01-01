import pytest
import redis
import time

# --- Configuration ---
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

@pytest.fixture(scope="module")
def redis_client():
    """Fixture to establish a Redis connection and flush the DB after tests."""
    client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    
    # Check connection before starting
    try:
        client.ping()
    except redis.ConnectionError:
        pytest.fail("Could not connect to Redis. Is the server running?")
        
    yield client
    
    # Cleanup: remove all keys used during testing
    client.flushdb()

# --- 1. Connection Tests ---
def test_redis_connection(redis_client):
    """Verifies the server is responsive."""
    assert redis_client.ping() is True

# --- 2. Basic Key-Value (String) Tests ---
def test_string_operations(redis_client):
    """Tests basic SET, GET, and DELETE."""
    redis_client.set("test_key", "hello_world")
    assert redis_client.get("test_key") == "hello_world"
    
    redis_client.delete("test_key")
    assert redis_client.get("test_key") is None

# --- 3. Complex Data Structures (Lists & Hashes) ---
def test_list_operations(redis_client):
    """Tests PUSH and POP logic."""
    redis_client.rpush("mylist", "item1", "item2")
    assert redis_client.llen("mylist") == 2
    assert redis_client.lpop("mylist") == "item1"

def test_hash_operations(redis_client):
    """Tests field-level updates in a Hash."""
    redis_client.hset("user:100", mapping={"name": "Alice", "score": "50"})
    assert redis_client.hget("user:100", "name") == "Alice"
    assert int(redis_client.hget("user:100", "score")) == 50

# --- 4. Expiration & TTL Tests ---
def test_key_expiration(redis_client):
    """Verifies that keys expire correctly."""
    redis_client.setex("temp_key", 1, "expires_fast") # Set with 1-second TTL
    assert redis_client.get("temp_key") == "expires_fast"
    
    time.sleep(1.1)
    assert redis_client.get("temp_key") is None

# --- 5. Atomic Operations ---
def test_increment(redis_client):
    """Tests atomic INCR operation."""
    redis_client.set("counter", 10)
    redis_client.incr("counter")
    assert int(redis_client.get("counter")) == 11
