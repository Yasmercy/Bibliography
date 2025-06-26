#!/usr/bin/env python

import click
import sys
import os
import io
import fileinput
import urllib.request
import bibtexparser

from contextlib import redirect_stdout
from pathlib import Path
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
@click.option("--cat", required = True, type = click.Path(file_okay = False, dir_okay = True, exists = True))
@click.option("--manual", required = False, type = bool, default = False, help = "Automatically find DOI entry")
@click.option("--doi", required = False, type = str, default = "")
@click.option("--name", required = False, type = str, default = "template")
@click.option("--title", required = False, type = str, default = "Title")
@click.option("--quiet", required = False, type = bool, default = False, help = "Disable print")
def generate(cat, manual, doi, name, title, quiet):
    with redirect_stdout(None if quiet else sys.stdout):
        if not manual:
            print("Adding bibtex entry...")
            bibtex = get_bibtex(doi)
            bibtex, name, title = parse(bibtex)
            with open("main/refs.bib", "r+") as f:
                library = f.read()
                if not duplicate_entry(library, name):
                    f.seek(0, io.SEEK_END)
                    f.write(write_string(bibtex))
                else:
                    print("Bibtex entry already exists, skipping...")

        print(f"Creating {cat}/{name}/main.tex...")
        with open("template/main.tex", "r") as f:
            text = f.read()
            text = text.replace("Title", title)
            text = text.replace("Body", f"~\\cite{{{name}}}")

        Path(f"{cat}/{name}").mkdir(exist_ok=True, parents=True)
        with open(f"{cat}/{name}/main.tex", "w") as f:
            f.write(text)

        print(f"Including {cat}/{name}/main...")
        for line in fileinput.FileInput("main/main.tex", inplace=True):
            # redirect stdout into main/main.tex
            if f"%{cat}" == line.strip():
                line = f"\\subfile{{../{cat}/{name}/main}}" + os.linesep + line
            sys.stdout.write(line)

        print("Done...")

if __name__ == "__main__":
    generate()
