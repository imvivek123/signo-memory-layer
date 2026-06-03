"""Simple Redis connection test for the Signo memory layer.

Run this file before starting the API to confirm that Redis is running and
the backend can set and get cached values.
"""

from memory.session_memory import get_redis_client


def test_redis_connection():
    """Connect to Redis, save a test value, and read it back."""

    try:
        redis_client = get_redis_client()

        test_key = "signo_redis_test"
        test_value = "Redis Connected Successfully"

        # Store a small test value for 60 seconds.
        redis_client.setex(test_key, 60, test_value)

        saved_value = redis_client.get(test_key)

        if saved_value == test_value:
            print("Redis Connected Successfully")
            print(f"Test value from Redis: {saved_value}")
        else:
            print("Redis connected, but the test value did not match.")

    except Exception as error:
        print("Redis connection failed.")
        print(f"Error: {error}")


if __name__ == "__main__":
    test_redis_connection()
