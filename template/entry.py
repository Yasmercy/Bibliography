#!/usr/bin/env python

import click
import sys
import io
import urllib.request
import bibtexparser

from contextlib import redirect_stdout
from urllib.error import HTTPError

from bibtexparser.model import Field
from bibtexparser import middlewares as mw
from bibtexparser import write_string

BASE_URL = 'http://dx.doi.org/'

def get_bibtex(doi: str):
    # https://scipython.com/blog/doi-to-bibtex/
    url = BASE_URL + doi
    req = urllib.request.Request(url)
    req.add_header('Accept', 'application/x-bibtex')
    try:
        with urllib.request.urlopen(req) as f:
            bibtex = f.read().decode()
            return bibtex
    except HTTPError as e:
        if e.code == 404:
            print('DOI not found, exiting...')
        else:
            print('Service unavailable, exiting...')
        sys.exit(1)

def parse(bibtex: str):
    library = bibtexparser.parse_string(
        bibtex,
        append_middleware=[
            mw.MonthIntMiddleware(True),
            mw.SeparateCoAuthors(),
            mw.SplitNameParts(),
        ],
    )
    entry = library.entries[0].fields_dict

    name = entry["author"]
    year = entry["year"]
    month = entry.get("month", Field("month", 0))

    name = f"{name.value[0].last[0].lower()}{int(year.value) % 100:02d}-{month.value:02d}"
    title = entry["title"].value

    library = bibtexparser.parse_string(
        bibtex,
        append_middleware=[ mw.MonthIntMiddleware(True), ],
    )
    library.entries[0].key = name
    return library, name, title

def duplicate_entry(bibtex: str, name: str):
    library = bibtexparser.parse_string(bibtex)
    return library.entries_dict.get(name) is not None

@click.command()
@click.option("--doi", required = False, type = str, default = "")
@click.option("--quiet", required = False, type = bool, default = False, help = "Disable print")
def generate(doi, quiet):
    with redirect_stdout(None if quiet else sys.stdout):
        print("Adding bibtex entry...")
        bibtex = get_bibtex(doi)
        bibtex, name, _ = parse(bibtex)
        with open("main/refs.bib", "r+") as f:
            library = f.read()
            if not duplicate_entry(library, name):
                f.seek(0, io.SEEK_END)
                f.write(write_string(bibtex))
            else:
                print("Bibtex entry already exists, skipping...")
        print(f"Created {name}, exiting...")

if __name__ == "__main__":
    generate()
