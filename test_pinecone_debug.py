"""Debug Pinecone semantic memory saving and searching.

Run this file from the project root:

    python test_pinecone_debug.py

This script checks three things:
1. The local sentence-transformers model can create an embedding.
2. Pinecone can find or create the configured index.
3. A vector can be saved and immediately searched.

It does not print API keys. Keep your Pinecone key only in the .env file.
"""

import os
import traceback

from dotenv import load_dotenv

from memory.vector_memory import get_embedding, save_memory, search_memories


TEST_PHONE_NUMBER = "+919876543210"
TEST_MEMORY_TEXT = "Driver complained about delayed payment issue"
TEST_SEARCH_QUERY = "payment problem happened again"


def print_section(title):
    """Print a clear divider so the debug output is easier to read."""

    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def check_environment():
    """Check whether the required .env values exist.

    This only checks if values are present. It does not prove the Pinecone key
    is valid, because that requires calling Pinecone.
    """

    print_section("1. Checking environment variables")

    pinecone_key = os.getenv("PINECONE_API_KEY")
    pinecone_index = os.getenv("PINECONE_INDEX")

    print("OpenAI API key required: NO")
    print("Embedding cost: FREE local sentence-transformers model")

    if pinecone_key:
        print("Pinecone API key found in .env: YES")
    else:
        print("Pinecone API key found in .env: NO")

    if pinecone_index:
        print(f"Pinecone index name found in .env: YES ({pinecone_index})")
    else:
        print("Pinecone index name found in .env: NO")


def check_local_embedding_model():
    """Check the local model by generating one real embedding."""

    print_section("2. Checking local embedding generation")

    try:
        print(f"Text to embed: {TEST_MEMORY_TEXT}")
        embedding = get_embedding(TEST_MEMORY_TEXT)

        if embedding is None:
            print("Local embedding success/failure: FAILURE")
            print("Embedding generated? NO")
            print("Reason: get_embedding returned None.")
            return None

        print("Local embedding success/failure: SUCCESS")
        print("Embedding generated? YES")
        print(f"Embedding length: {len(embedding)}")

        if len(embedding) == 384:
            print("Embedding dimension check: OK, expected 384")
        else:
            print("Embedding dimension check: WARNING, expected 384")

        return embedding

    except Exception as error:
        print("Local embedding success/failure: FAILURE")
        print(f"Local embedding error: {error}")
        print("Full traceback:")
        traceback.print_exc()
        return None


def check_pinecone_connection():
    """Check whether Pinecone is reachable and whether the index exists.

    The save_memory function can create the index automatically. This separate
    check is here only to make debugging clearer.
    """

    print_section("3. Checking Pinecone connection and index")

    try:
        from pinecone import Pinecone

        api_key = os.getenv("PINECONE_API_KEY")
        index_name = os.getenv("PINECONE_INDEX", "signo-memory")

        if not api_key:
            print("Pinecone connection success/failure: FAILURE")
            print("Reason: PINECONE_API_KEY is missing.")
            return False

        pinecone_client = Pinecone(api_key=api_key)
        index_list = pinecone_client.list_indexes()

        if hasattr(index_list, "names"):
            index_names = index_list.names()
        else:
            index_names = [
                index.get("name") if isinstance(index, dict) else index.name
                for index in index_list
            ]

        print("Pinecone connection success/failure: SUCCESS")
        print(f"Configured index name: {index_name}")
        print(f"Indexes found in Pinecone: {index_names}")

        if index_name in index_names:
            print("Index found or not: FOUND")
        else:
            print("Index found or not: NOT FOUND")
            print("save_memory should try to create it automatically.")

        return True

    except ModuleNotFoundError:
        print("Pinecone connection success/failure: FAILURE")
        print("Reason: pinecone package is not installed.")
        print("Fix: pip install -r requirements.txt")
        return False

    except Exception as error:
        print("Pinecone connection success/failure: FAILURE")
        print(f"Pinecone error: {error}")
        print("Full traceback:")
        traceback.print_exc()
        return False


def debug_save_memory():
    """Save one test memory into Pinecone and print the full response."""

    print_section("4. Saving semantic memory into Pinecone")

    try:
        metadata = {
            "intent": "payment_issue",
            "sentiment": "negative",
        }

        print(f"Phone number: {TEST_PHONE_NUMBER}")
        print(f"Memory text: {TEST_MEMORY_TEXT}")
        print(f"Metadata: {metadata}")

        save_response = save_memory(
            phone_number=TEST_PHONE_NUMBER,
            text=TEST_MEMORY_TEXT,
            metadata=metadata,
        )

        print("Full save response:")
        print(save_response)

        if save_response is None:
            print("Vector saved or not: NOT SAVED")
            print("Reason: save_memory returned None.")
        else:
            print("Vector saved or not: SAVED")

        return save_response

    except Exception as error:
        print("Vector saved or not: NOT SAVED")
        print(f"Save error: {error}")
        print("Full traceback:")
        traceback.print_exc()
        return None


def debug_search_memories():
    """Search Pinecone immediately after saving the test memory."""

    print_section("5. Searching semantic memories")

    try:
        print(f"Phone number: {TEST_PHONE_NUMBER}")
        print(f"Search query: {TEST_SEARCH_QUERY}")

        search_results = search_memories(
            phone_number=TEST_PHONE_NUMBER,
            query=TEST_SEARCH_QUERY,
        )

        print("Full semantic search results:")
        print(search_results)

        if search_results:
            print(f"Semantic matches found: YES ({len(search_results)})")
        else:
            print("Semantic matches found: NO")
            print("Note: Pinecone can sometimes need a short moment after upsert.")

        return search_results

    except Exception as error:
        print("Semantic search success/failure: FAILURE")
        print(f"Search error: {error}")
        print("Full traceback:")
        traceback.print_exc()
        return []


def main():
    """Run the full Pinecone semantic memory debug flow."""

    print_section("Pinecone Semantic Memory Debug Test")
    print("Starting debug test...")

    load_dotenv()

    check_environment()
    embedding = check_local_embedding_model()
    pinecone_is_reachable = check_pinecone_connection()

    if embedding is None:
        print("\nStopping early because local embedding generation failed.")
        return

    if not pinecone_is_reachable:
        print("\nStopping early because Pinecone connection failed.")
        return

    save_response = debug_save_memory()

    if save_response is None:
        print("\nStopping early because vector save failed.")
        return

    debug_search_memories()

    print_section("Debug test complete")
    print("If a match appears above, Pinecone semantic memory is working.")


if __name__ == "__main__":
    main()
