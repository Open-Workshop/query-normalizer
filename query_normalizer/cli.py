"""CLI interface for query normalization."""

import argparse
import sys

from query_normalizer import QueryNormalizer


def cli() -> None:
    parser = argparse.ArgumentParser(
        description="Normalize search queries for classic search and embedding models"
    )
    parser.add_argument("query", nargs="+", help="Search query to normalize")
    parser.add_argument(
        "--mode",
        choices=["classic", "embedding", "both"],
        default="both",
        help="Normalization mode (default: both)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show corrections applied",
    )

    args = parser.parse_args()
    query = " ".join(args.query)
    normalizer = QueryNormalizer()

    if args.mode == "classic":
        result = normalizer.normalize_for_classic(query)
        print(f"Normalized: {result.normalized_query}")
        if args.debug and result.corrections_applied:
            print("Corrections:")
            for correction in result.corrections_applied:
                print(f"  - {correction}")
    elif args.mode == "embedding":
        result = normalizer.normalize_for_embedding(query)
        print(f"Normalized: {result.normalized_query}")
        if args.debug and result.corrections_applied:
            print("Corrections:")
            for correction in result.corrections_applied:
                print(f"  - {correction}")
    else:
        classic = normalizer.normalize_for_classic(query)
        embedding = normalizer.normalize_for_embedding(query)

        print(f"Classic: {classic.normalized_query}")
        print(f"Embedding: {embedding.normalized_query}")

        if args.debug:
            if classic.corrections_applied:
                print("Classic corrections:")
                for correction in classic.corrections_applied:
                    print(f"  - {correction}")
            if embedding.corrections_applied:
                print("Embedding corrections:")
                for correction in embedding.corrections_applied:
                    print(f"  - {correction}")


if __name__ == "__main__":
    cli()
