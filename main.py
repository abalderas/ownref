# main.py
import argparse
import sys
import bibtexparser
import re


def _unescape_latex(s: str) -> str:
    # Converts simple LaTeX sequences to Unicode and removes braces.
    if not s:
        return s
    s = s.replace('\n', ' ')

    # Accent mapping
    accents = {
        "a":"á","e":"é","i":"í","o":"ó","u":"ú","A":"Á","E":"É","I":"Í","O":"Ó","U":"Ú",
        "n":"ñ","N":"Ñ"
    }

    # 1. Handle \'x and \'\\x sequences (acute accent)
    s = re.sub(r"\\'\\?([A-Za-z])", lambda m: accents.get(m.group(1), m.group(1)), s)

    # 2. Handle other sequences:
    # \`x (grave accent)
    s = re.sub(r"\\`([A-Za-z])", lambda m: m.group(1), s)
    # \~x (tilde)
    s = re.sub(r"\\~([nN])", lambda m: "ñ" if m.group(1) == "n" else "Ñ", s)
    # \"x (umlaut)
    s = re.sub(r'\\"([A-Za-z])', lambda m: {"o":"ö","O":"Ö"}.get(m.group(1), m.group(1)), s)

    # Remove residual braces
    s = s.replace('{', '').replace('}', '')

    # Collapse spaces
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def _parse_bib_fields(paper: str) -> dict:
    fields = {}
    if not paper:
        return fields

    try:
        # Use bibtexparser for robust parsing
        db = bibtexparser.loads(paper)
        if db.entries:
            # Process the first entry
            entry = db.entries[0]
            # Convert keys to lowercase
            fields = {k.lower(): v for k, v in entry.items()}

    except Exception as e:
        print(f"Error parsing BibTeX with bibtexparser: {e}", file=sys.stderr)

    return fields

def _format_authors_apa(authors_field: str) -> str:
    if not authors_field:
        return ""
    # Split by ' and '
    parts = re.split(r'\s+and\s+', authors_field)
    names = []
    for p in parts:
        p = _unescape_latex(p.strip())
        if ',' in p:
            last, first = [x.strip() for x in p.split(',', 1)]
        else:
            tokens = p.split()
            if len(tokens) == 1:
                last = tokens[0]; first = ""
            else:
                last = tokens[-1]; first = " ".join(tokens[:-1])
        # Generate initials
        initials = ""
        for token in first.split():
            if token:
                initials += f" {token[0]}."
        initials = initials.strip()
        if initials:
            names.append(f"{last}, {initials}")
        else:
            names.append(f"{last}")
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]}, & {names[1]}"
    return f"{', '.join(names[:-1])}, & {names[-1]}"

def PaperFromBib(paper: str) -> None:
    """
    Prints the APA style reference from a BibTeX entry.
    """
    fields = _parse_bib_fields(paper)

    authors = _format_authors_apa(fields.get('author', ''))
    year = _unescape_latex(fields.get('year', '')).strip()
    title = _unescape_latex(fields.get('title', '')).strip()
    journal = _unescape_latex(fields.get('journal', '')).strip()
    volume = _unescape_latex(fields.get('volume', '')).strip()
    number = _unescape_latex(fields.get('number', '')).strip()
    # Build journal/volume(number) part
    journal_part = journal
    vol_part = ""
    if volume:
        vol_part = volume
        if number:
            vol_part = f"{volume}({number})"
    elif number:
        vol_part = f"({number})"
    if vol_part:
        if journal_part:
            journal_part = f"{journal_part}, {vol_part}"
        else:
            journal_part = vol_part
    # Format output
    apa = ""
    if authors:
        apa += f"{authors} "
    if year:
        apa += f"({year}). "
    if title:
        apa += f"{title}. "
    if journal_part:
        apa += f"{journal_part}."
    apa = re.sub(r'\s+', ' ', apa).strip()
    print(apa)


def main():
    parser = argparse.ArgumentParser(description="Prints a BibTeX entry using PaperFromBib")
    parser.add_argument("file", nargs="?", help="Path to a .bib file (optional)")
    parser.add_argument("--text", "-t", help="BibTeX string directly")
    args = parser.parse_args()

    if args.text:
        PaperFromBib(args.text)
        return

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                PaperFromBib(f.read())
        except Exception as e:
            print(f"Error reading ` {args.file} `: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # Use stdin data if available (e.g., pipe)
    if not sys.stdin.isatty():
        PaperFromBib(sys.stdin.read())
        return

    parser.print_help()
    sys.exit(0)

if __name__ == "__main__":
    main()