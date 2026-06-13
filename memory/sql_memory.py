"""Reusable PostgreSQL memory helpers for the Signo AI backend.

This file keeps all direct database access in one place.
The FastAPI routes can import these functions instead of writing SQL directly.
"""

import os
from datetime import date, datetime
from decimal import Decimal

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor


# Load database settings from the .env file.
# This keeps passwords and machine-specific settings out of the Python code.
load_dotenv()


def get_connection():
    """Create and return a new PostgreSQL database connection.

    Each caller should close the connection when it is finished.
    Keeping connection creation in one function makes the rest of the project
    cleaner and easier to update later.
    """

    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )


def _clean_value(value):
    """Convert database values into JSON-friendly Python values.

    PostgreSQL DECIMAL values are returned as Decimal objects by psycopg2.
    PostgreSQL timestamp/date values are returned as datetime/date objects.
    Converting them here keeps FastAPI responses and Redis JSON caching simple.
    """

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    return value


def _clean_row(row):
    """Convert one database row into a normal JSON-friendly dictionary."""

    if row is None:
        return None

    return {key: _clean_value(value) for key, value in row.items()}


def _clean_rows(rows):
    """Convert many database rows into JSON-friendly dictionaries."""

    return [_clean_row(row) for row in rows]


def _ensure_clean_call_log_columns(cursor):
    """Add compressed conversational-memory columns if the database is older.

    The app stores only cleaned memory fields. Raw OmniDimension metadata,
    interactions, recordings, and bot messages are intentionally not inserted.
    """

    alter_query = """
        ALTER TABLE call_logs
        ADD COLUMN IF NOT EXISTS conversation_summary TEXT,
        ADD COLUMN IF NOT EXISTS issue_category TEXT,
        ADD COLUMN IF NOT EXISTS issue_summary TEXT,
        ADD COLUMN IF NOT EXISTS language VARCHAR(20),
        ADD COLUMN IF NOT EXISTS important BOOLEAN DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS follow_up_required BOOLEAN DEFAULT FALSE;
    """

    cursor.execute(alter_query)


def get_driver_by_phone(phone_number):
    """Fetch one driver from the drivers table by phone number.

    Args:
        phone_number: The driver's phone number from the API path.

    Returns:
        A dictionary with driver details if found, otherwise None.
    """

    connection = None
    cursor = None

    try:
        connection = get_connection()

        # RealDictCursor returns rows as dictionaries instead of tuples.
        # This makes API responses easier to build and easier to understand.
        cursor = connection.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT driver_id, phone_number, name, truck_number, preferred_language
            FROM drivers
            WHERE phone_number = %s
            LIMIT 1;
        """

        # Always pass query values separately instead of formatting strings.
        # This helps protect the app from SQL injection.
        cursor.execute(query, (phone_number,))
        row = cursor.fetchone()

        return _clean_row(row)

    except Exception as error:
        print(f"Error fetching driver by phone number: {error}")
        return None

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


def create_driver(
    phone_number: str,
    name: str = "Unknown Driver",
    truck_number: str = None,
    preferred_language: str = "English",
):
    """Create a new driver profile and return the saved row.

    This is used when OmniDimension sends a phone number that PostgreSQL has
    never seen before. The memory workflow can then continue instead of failing
    just because the driver profile did not already exist.
    """

    connection = None
    cursor = None

    try:
        print(f"Creating driver profile for phone number: {phone_number}")

        connection = get_connection()
        cursor = connection.cursor(cursor_factory=RealDictCursor)

        query = """
            INSERT INTO drivers (
                phone_number,
                name,
                truck_number,
                preferred_language
            )
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (phone_number)
            DO UPDATE SET phone_number = EXCLUDED.phone_number
            RETURNING driver_id, phone_number, name, truck_number, preferred_language;
        """

        cursor.execute(
            query,
            (
                phone_number,
                name,
                truck_number,
                preferred_language,
            ),
        )

        saved_row = cursor.fetchone()
        connection.commit()

        print("Driver profile created successfully.")
        return _clean_row(saved_row)

    except Exception as error:
        print(f"Error creating driver profile: {error}")

        if connection is not None:
            connection.rollback()

        return None

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


def get_driver_payments(driver_id):
    """Fetch all payment rows for a single driver.

    Args:
        driver_id: The primary key from the drivers table.

    Returns:
        A list of payment dictionaries. Returns an empty list if none exist
        or if a database error occurs.
    """

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT payment_id, driver_id, amount, status, payment_date
            FROM payments
            WHERE driver_id = %s
            ORDER BY payment_id DESC;
        """

        cursor.execute(query, (driver_id,))
        rows = cursor.fetchall()

        return _clean_rows(rows)

    except Exception as error:
        print(f"Error fetching driver payments: {error}")
        return []

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


def get_open_tickets(driver_id):
    """Fetch open support tickets for a single driver.

    Args:
        driver_id: The primary key from the drivers table.

    Returns:
        A list of open support ticket dictionaries. Returns an empty list if
        none exist or if a database error occurs.
    """

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT ticket_id, driver_id, issue, status
            FROM support_tickets
            WHERE driver_id = %s
              AND LOWER(status) = 'open'
            ORDER BY ticket_id DESC;
        """

        cursor.execute(query, (driver_id,))
        rows = cursor.fetchall()

        return _clean_rows(rows)

    except Exception as error:
        print(f"Error fetching open support tickets: {error}")
        return []

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


def get_recent_call_logs(phone_number):
    """Fetch recent conversation summaries for one phone number."""

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT
                issue_summary,
                conversation_summary,
                created_at
            FROM call_logs
            WHERE phone_number = %s
            ORDER BY created_at DESC
            LIMIT 5;
        """

        cursor.execute(query, (phone_number,))
        rows = cursor.fetchall()

        return _clean_rows(rows)

    except Exception as error:
        print(f"Error fetching recent call logs: {error}")
        return []

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


def save_call_log(driver_id, compressed_memory):
    """Store one compressed conversational memory in the call_logs table.

    Args:
        driver_id: Internal PostgreSQL driver id linked to this call.
        compressed_memory: Clean memory object produced by extract_memory().

    Returns:
        A dictionary containing the saved clean call log row, or None.
    """

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        _ensure_clean_call_log_columns(cursor)

        phone_number = compressed_memory.get("phone_number", "")
        language = compressed_memory.get("language", "")
        issue_category = compressed_memory.get("issue_category", "")
        issue_summary = compressed_memory.get("issue_summary", "")
        conversation_summary = compressed_memory.get("conversation_summary", "")
        call_summary = compressed_memory.get("call_summary", "")
        sentiment = compressed_memory.get("sentiment", "")
        important = compressed_memory.get("important", False)
        follow_up_required = compressed_memory.get("follow_up_required", False)

        query = """
            INSERT INTO call_logs (
                driver_id,
                phone_number,
                language,
                issue_category,
                issue_summary,
                conversation_summary,
                call_summary,
                sentiment,
                important,
                follow_up_required
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING
                call_log_id,
                driver_id,
                phone_number,
                language,
                issue_category,
                issue_summary,
                conversation_summary,
                call_summary,
                sentiment,
                important,
                follow_up_required,
                created_at;
        """

        cursor.execute(
            query,
            (
                driver_id,
                phone_number,
                language,
                issue_category,
                issue_summary,
                conversation_summary,
                call_summary,
                sentiment,
                important,
                follow_up_required,
            ),
        )

        saved_row = cursor.fetchone()

        # INSERT, UPDATE, and DELETE queries must be committed.
        # Without commit(), PostgreSQL will not permanently save the data.
        connection.commit()

        print("[PostgreSQL] Clean conversational memory saved.")
        return _clean_row(saved_row)

    except Exception as error:
        print(f"Error saving call log: {error}")

        if connection is not None:
            connection.rollback()

        return None

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()
