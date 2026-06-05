#!/usr/bin/env python3

import argparse

from rich.console import Console
from rich.markdown import Markdown as Markdown2

from garner.dictionary import DEFAULT_DB, DEFAULT_DEFINITIONS, build, list_essays, lookup, search


MAX_RESULTS_SHOWN = 10
LOOKUP_SUGGESTIONS_SHOWN = 2


def display(row, rows, verbose, plain):
    console = Console()

    if row:
        if verbose:
            console.print("filename: " + row["filename"])

        if plain:
            console.print(row["body_plain"])
        else:
            console.print(Markdown2(row["body_markdown"]))

    if rows:
        if row:
            print("\n\n")
        if verbose:
            for row in rows:
                console.print(f"{row['headword']} ({row['sort_key']}) @ {row['filename']} {' (essay)' if row['is_essay'] else ''}")
        else:
            for row in rows:
                console.print(f"{row['headword']} {' (essay)' if row['is_essay'] else ''}")

    if not row and not rows:
        print(f"No entry found")


def display_lookup_suggestions(word, rows, verbose):
    if not rows:
        print(f"No entry found")
        return

    print(f"No exact entry found for {word}. Did you mean:")
    display(None, rows, verbose, plain=True)


def main():
    parser = argparse.ArgumentParser(
        prog="garner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Look up entries from Garner's English usage dictionary.\n"
            "A usage dictionary helps writers and editors make practical choices about contested English usage."
        ),
        epilog=(
            "Notes:\n"
            "  Language-Change Index: Garner's 1-5 scale for how accepted a disputed usage has become.\n"
            "  Current ratio: a print-frequency snapshot comparing a prevalent form with a variant.\n\n"
            "Examples:\n"
            "  garner --build\n"
            "  garner affect\n"
            "  garner hypercorrection essay\n"
            "  garner --search accomodate\n"
            "  garner --search hypercorrection essay\n"
            "  garner --search affect --maxresults 3\n"
            "  garner --essays\n"
        ),
    )

    global_options = parser.add_argument_group("global options")
    command_options = parser.add_argument_group("commands")
    search_options = parser.add_argument_group("search options")
    output_options = parser.add_argument_group("output options")
    lookup_args = parser.add_argument_group("lookup")

    global_options.add_argument(
        "-d", "--db",
        default=str(DEFAULT_DB),
        help=f"SQLite database path; default: {DEFAULT_DB}",
    )

    command_options.add_argument(
        "-b", "--build",
        nargs="?",
        const=True,
        metavar="DIR",
        help=f"Build the database from definition files; default: {DEFAULT_DEFINITIONS}",
    )

    command_options.add_argument(
        "-e", "--essays",
        action="store_true",
        help="List the \"essays\" in this dictionary",
    )

    command_options.add_argument(
        "-s", "--search",
        help="Search for a word instead of doing a straight lookup. Extra words are joined into the search query.",
    )

    search_options.add_argument(
        "-m", "--maxresults",
        default=None,
        type=int,
        help=f"Maximum search results to return; only used with --search; default: {MAX_RESULTS_SHOWN}",
    )

    output_options.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )

    output_options.add_argument(
        "-p", "--plain",
        action="store_true",
        help="Output plain text, no fancy styling.",
    )

    lookup_args.add_argument(
        "word",
        nargs="*",
        help="Word to look up. If multiple words are passed in, they will be joined into one lookup.",
    )

    args = parser.parse_args()

    if args.maxresults is not None and args.search is None:
        parser.error("--maxresults can only be used with --search")

    if args.build is not None:
        if args.build is True:
            source_dir = DEFAULT_DEFINITIONS
        else:
            source_dir = args.build
        build(source_dir, args.db, args.verbose)

    elif args.search is not None:
        search_terms = [args.search] + args.word
        max_results = args.maxresults or MAX_RESULTS_SHOWN
        rows = search(" ".join(search_terms), max_results, args.db)
        display(None, rows, args.verbose, args.plain)

    elif args.essays is True:
        rows = list_essays(args.db)
        display(None, rows, args.verbose, args.plain)

    elif args.word:
        word = " ".join(args.word)
        row = lookup(word, args.db)

        if row:
            display(row, None, args.verbose, args.plain)

            if row["forwarding"]:
                print("\n")
                row = lookup(row["forwarding"], args.db)
                display(row, None, args.verbose, args.plain)
        else:
            rows = search(word, LOOKUP_SUGGESTIONS_SHOWN, args.db)
            display_lookup_suggestions(word, rows, args.verbose)

    else:
        parser.print_help()
        parser.exit(1)


if __name__ == "__main__":
    main()
