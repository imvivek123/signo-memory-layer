"""Simple PostgreSQL connection test for the Signo memory layer.

Run this file before starting the API to confirm that:
1. Your .env file is configured correctly.
2. PostgreSQL is running.
3. The drivers table can be queried.
"""

import os

import psycopg2
from dotenv import load_dotenv


# Load environment variables from .env.
# Example: DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
load_dotenv()


def test_database_connection():
    """Connect to PostgreSQL and print all rows from the drivers table."""

    connection = None
    cursor = None

    try:
        connection = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
        )

        cursor = connection.cursor()

        print("Database Connected Successfully")
        print("")
        print("Drivers table rows:")

        cursor.execute(
            """
            SELECT driver_id, phone_number, name, truck_number, preferred_language
            FROM drivers
            ORDER BY driver_id;
            """
        )

        rows = cursor.fetchall()

        if not rows:
            print("No drivers found.")

        for row in rows:
            driver_id, phone_number, name, truck_number, preferred_language = row
            print(
                f"Driver ID: {driver_id} | "
                f"Phone: {phone_number} | "
                f"Name: {name} | "
                f"Truck: {truck_number} | "
                f"Language: {preferred_language}"
            )

    except Exception as error:
        print("Database connection failed.")
        print(f"Error: {error}")

    finally:
        # Always close database resources, even when an error happens.
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


if __name__ == "__main__":
    test_database_connection()
