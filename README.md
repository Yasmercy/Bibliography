# Annotated Bibliography

Scripting to reduce friction when managing a megafile for papers.
Uses the [subfiles](https://ctan.org/pkg/subfiles?lang=en) package, so each paper goes in its own document.

# Structure

```
> main
    | main.tex
    | refs.bib
> template
    | main.tex
    | entry.py
    | generate.py
> category 1... 
    | papers go here...
> other categories...
    | ...
```

# Usage

Add new references into the bibliography with just the doi (searches through [https://dx.doi.org/])
```
python template/entry.py --doi [doi]
```

Also, can add files for further commentary and notes.
This create copy `template/main.tex` to `cat/lastNameYear-Month/main.tex`.
```
python template/generate.py --doi [doi] --cat [category]
```

You can also add the `--manual True` flag to generate the template, skipping the online doi search.
