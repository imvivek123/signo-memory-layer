"""Redis session-memory helpers for the Signo AI backend.

PostgreSQL is the permanent structured memory store.
Redis is the temporary fast cache used during active or recent sessions.
"""

import json
import os

import redis
from dotenv import load_dotenv


# Load Redis settings from the .env file.
# Example: REDIS_HOST=localhost and REDIS_PORT=6379
load_dotenv()


# Driver memory should be refreshed often, so cache it only briefly.
# 300 seconds means cached driver memory expires after 5 minutes.
SESSION_EXPIRATION_SECONDS = 300


def get_redis_client():
    """Create and return a Redis client.

    decode_responses=True makes Redis return normal Python strings instead of
    bytes. That keeps JSON loading simple for beginners.
    """

    return redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        decode_responses=True,
    )


def _session_key(phone_number):
    """Create one consistent Redis key for a driver's session memory."""

    return f"driver_session:{phone_number}"


def get_session(phone_number):
    """Read cached driver memory from Redis.

    Args:
        phone_number: Driver phone number from the API path.

    Returns:
        A dictionary if cached data exists, otherwise None.
    """

    try:
        redis_client = get_redis_client()
        cached_value = redis_client.get(_session_key(phone_number))

        if cached_value is None:
            return None

        # Redis stores strings, so we convert the JSON string back to a dict.
        return json.loads(cached_value)

    except Exception as error:
        print(f"Redis get_session error: {error}")
        return None


def set_session(phone_number, data):
    """Save driver memory in Redis for a short time.

    Args:
        phone_number: Driver phone number from the API path.
        data: Dictionary containing driver, payments, and open tickets.

    Returns:
        True if the value was saved, otherwise False.
    """

    try:
        redis_client = get_redis_client()

        # json.dumps converts Python dictionaries and lists into a string that
        # Redis can store. default=str protects us from datetime values.
        serialized_data = json.dumps(data, default=str)

        redis_client.setex(
            _session_key(phone_number),
            SESSION_EXPIRATION_SECONDS,
            serialized_data,
        )

        return True

    except Exception as error:
        print(f"Redis set_session error: {error}")
        return False


def clear_session(phone_number):
    """Remove one driver's cached session memory from Redis.

    This is useful when you know the driver data changed and want the next API
    call to fetch fresh data from PostgreSQL.
    """

    try:
        redis_client = get_redis_client()
        redis_client.delete(_session_key(phone_number))
        return True

    except Exception as error:
        print(f"Redis clear_session error: {error}")
        return False
