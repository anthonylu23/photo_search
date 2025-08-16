import argparse
import os
import sys


def connect_client(persist_path):
    try:
        import chromadb
        if hasattr(chromadb, "PersistentClient"):
            return chromadb.PersistentClient(path=persist_path)
        # Fallback for older chromadb versions
        from chromadb.config import Settings
        return chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=persist_path))
    except Exception as exc:
        print(f"Failed to initialize Chroma client for path '{persist_path}': {exc}")
        sys.exit(1)


def list_and_display(client, collection_name=None, limit=10):
    def _print_collection(col):
        try:
            name = getattr(col, "name", "<unknown>")
            count = col.count()
            print(f"\nCollection: {name} (count={count})")
            if count == 0:
                return
            result = col.get(include=["metadatas", "uris"], limit=limit)
            ids = result.get("ids", []) or []
            uris = result.get("uris", []) or []
            metadatas = result.get("metadatas", []) or []
            for idx, item_id in enumerate(ids):
                print(f"  - id: {item_id}")
                uri = uris[idx] if idx < len(uris) else None
                if uri:
                    print(f"    uri: {uri}")
                md = metadatas[idx] if idx < len(metadatas) else {}
                if not md:
                    print("    metadata: {}")
                else:
                    for k, v in md.items():
                        print(f"    {k}: {v}")
        except Exception as exc:
            print(f"Error reading collection '{getattr(col, 'name', '<unknown>')}': {exc}")

    if collection_name:
        col = client.get_collection(collection_name)
        _print_collection(col)
    else:
        cols = client.list_collections()
        if not cols:
            print("No collections found.")
            return
        for col in cols:
            _print_collection(col)


def main():
    parser = argparse.ArgumentParser(description="Display contents of a persisted ChromaDB directory.")
    parser.add_argument("--path", default="./chroma_langchain_db", help="Persist directory path (default: ./chroma_langchain_db)")
    parser.add_argument("--collection", default=None, help="Specific collection name to show (default: all)")
    parser.add_argument("--limit", type=int, default=10, help="Max items to display per collection (default: 10)")
    args = parser.parse_args()

    persist_path = args.path
    if not os.path.isdir(persist_path):
        print(f"Persist directory not found: {persist_path}")
        sys.exit(1)

    client = connect_client(persist_path)
    list_and_display(client, collection_name=args.collection, limit=args.limit)


if __name__ == "__main__":
    main()


