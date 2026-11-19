#!/usr/bin/env python3
"""Build supplementary tables from the latest manuscript: citation order, then one CSV per LaTeX table.

    python3 supptables_from_tex.py order main.tex [manuscript.docx ...]
    python3 supptables_from_tex.py table main.tex --label tab:hyperparameters --out Supplementary_Table_3_hyperparameters.csv \
        --header "Setting,Value,Reason" [--group-column Group] [--cites cites.tsv]
    python3 supptables_from_tex.py --self-test

order: lists every supplementary table the manuscript cites, with the number of citations and the order of first
citation, which is the order tables are numbered in. Reads .tex (comments removed; matches
`Supplementary Table~\\ref{<label>}`), .docx (the text of word/document.xml; matches `Supplementary Table <N>`) and
plain text. Give the TeX and the exported online document side by side to see where they disagree.

table: extracts the tabular or longtable that carries `\\label{<label>}` and writes its data rows as CSV. Rows
that are a single `\\multicolumn` become a group title written into --group-column. Citation keys are replaced by
the text given in --cites (a TSV: key, then author-year plus accession); a citation with a key missing from the
map fails the run, so no key is silently dropped. The run fails when any LaTeX is left in a cell or a row has the
wrong number of cells. Output is UTF-8 with `\\n` line ends, so a rerun on the same source is byte-identical.

Exit 0 on success, 1 on a failed check, 2 on bad arguments. Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import io
import re
import sys
import tempfile
import zipfile
from pathlib import Path

TEX_CITE = re.compile(r"Supplementary\s+Tables?~?\s*\\ref\{([^{}]+)\}")
TEXT_CITE = re.compile(r"Supplementary\s+Tables?\s+(\d+[A-Za-z]?)")


# ----------------------------------------------------------------------------- reading
def read_tex(path: Path) -> str:
    """TeX source with comments removed (an unescaped % to the end of the line)."""
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.search(r"(?<!\\)%", line)
        out.append(line[: m.start()] if m else line)
    return "\n".join(out)


def read_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<w:tab/>", "\t", xml)
    text = re.sub(r"<[^>]+>", "", xml)
    for ent, ch in (("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&apos;", "'"), ("&amp;", "&")):
        text = text.replace(ent, ch)
    return text


def read_any(path: Path) -> tuple:
    if path.suffix == ".tex":
        return read_tex(path), TEX_CITE
    if path.suffix == ".docx":
        return read_docx(path), TEXT_CITE
    return path.read_text(encoding="utf-8"), TEXT_CITE


def citation_order(text: str, pattern) -> list:
    """[(label, count, first_position)] in order of first citation."""
    seen = {}
    for m in pattern.finditer(text):
        for label in m.group(1).split(","):
            label = label.strip()
            pos, n = seen.get(label, (m.start(), 0))
            seen[label] = (pos, n + 1)
    return sorted(((k, n, pos) for k, (pos, n) in seen.items()), key=lambda r: r[2])


# ----------------------------------------------------------------------------- TeX tables
def brace_groups(s: str, i: int, n: int) -> tuple:
    """The n consecutive {...} groups starting at s[i] (spaces skipped); returns (groups, end)."""
    groups = []
    for _ in range(n):
        while s[i].isspace():
            i += 1
        if s[i] != "{":
            raise ValueError("expected '{' at: " + s[i: i + 40])
        depth, j = 0, i
        while True:
            if s[j] == "{" and s[j - 1] != "\\":
                depth += 1
            elif s[j] == "}" and s[j - 1] != "\\":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        groups.append(s[i + 1: j])
        i = j + 1
    return groups, i


def replace_cmd(s: str, name: str, nargs: int = 1, keep=0) -> str:
    """Replace \\name{a1}..{an} by argument `keep` (None drops the command)."""
    tag = "\\" + name + "{"
    out, i = [], 0
    while True:
        k = s.find(tag, i)
        if k < 0:
            out.append(s[i:])
            return "".join(out)
        out.append(s[i:k])
        groups, i = brace_groups(s, k + len(tag) - 1, nargs)
        if keep is not None:
            out.append(groups[keep])


def table_body(tex: str, label: str) -> str:
    """Data rows of the tabular or longtable that carries \\label{label}."""
    pos = tex.find("\\label{%s}" % label)
    if pos < 0:
        raise ValueError(f"label {label} not found")
    end_m = re.compile(r"\\end\{(tabular\*?|longtable)\}").search(tex, pos)
    if not end_m:
        raise ValueError(f"no table end after label {label}")
    seg = tex[pos: end_m.start()]
    for marker in ("\\endlastfoot", "\\endhead"):
        if marker in seg:
            seg = seg[seg.rindex(marker) + len(marker):]
            break
    else:
        if "\\midrule" in seg:
            seg = seg[seg.index("\\midrule") + len("\\midrule"):]
        elif "\\hline" in seg:
            seg = seg[seg.index("\\hline") + len("\\hline"):]
    return seg.split("\\bottomrule")[0]


def split_rows(body: str) -> list:
    rows = []
    for raw in re.split(r"\\\\(?:\[[^\]]*\])?", body):
        r = re.sub(r"^(\s*\\(midrule|addlinespace|hline|cmidrule\{[^}]*\})(\[[^\]]*\])?)+", "", raw).strip()
        if r:
            rows.append(r)
    return rows


def split_cells(row: str) -> list:
    return [c.strip() for c in re.split(r"(?<!\\)&", row)]


def math(s: str) -> str:
    s = s.replace("~", " ")
    s = re.sub(r"\\mathrm\{([^{}]*)\}", r"\1", s)
    s = s.replace("\\{", "{").replace("\\}", "}").replace("\\%", "%")
    for cmd, sym in (("geq", "\u2265 "), ("leq", "\u2264 "), ("sim", "~"), ("times", " \u00d7 "),
                     ("pm", "\u00b1"), ("alpha", "\u03b1"), ("beta", "\u03b2"), ("lambda", "\u03bb"),
                     ("mu", "\u00b5"), ("rho", "\u03c1"), ("in", " \u2208 ")):
        s = re.sub(r"\\%s(?![A-Za-z])\s*" % cmd, sym, s)
    s = re.sub(r"([_^])\{([^{}]*)\}", r"\1\2", s)
    s = re.sub(r"\s*=\s*", " = ", s)
    return re.sub(r"\s+", " ", s).strip()


def clean(s: str, cites: dict) -> str:
    """One LaTeX cell to plain text; raises ValueError when LaTeX is left over."""
    s = replace_cmd(s, "href", 2, keep=1)
    s = replace_cmd(s, "url", 1, keep=0)

    def cite(m):
        keys = [k.strip() for k in m.group(1).split(",")]
        missing = [k for k in keys if k not in cites]
        if missing:
            raise ValueError("citation keys missing from --cites: " + ", ".join(missing))
        return " (" + "; ".join(cites[k] for k in keys) + ")"

    s = re.sub(r"~?\\cite[pt]?\{([^{}]*)\}", cite, s)
    for cmd in ("textbf", "textit", "texttt", "emph", "text", "mbox"):
        s = replace_cmd(s, cmd)
    s = s.replace("~", " ")
    s = re.sub(r"\\\((.*?)\\\)", lambda m: math(m.group(1)), s)
    s = re.sub(r"\$(.*?)\$", lambda m: math(m.group(1)), s)
    s = s.replace("{,}", ",").replace("\\,", " ")
    s = s.replace("---", "\u2014").replace("--", "\u2013")
    s = s.replace("\\_", "_").replace("\\&", "&").replace("\\%", "%").replace("\\#", "#")
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\s+([,.;)])", r"\1", s)
    if re.search(r"[\\$]", s):
        raise ValueError("LaTeX left in cell: " + s[:80])
    return s


def group_title(row: str, cites: dict):
    if not row.startswith("\\multicolumn"):
        return None
    (_, _, content), _ = brace_groups(row, len("\\multicolumn"), 3)
    return clean(content, cites)


def extract(tex: str, label: str, cites: dict, grouped: bool) -> list:
    rows, group = [], ""
    for row in split_rows(table_body(tex, label)):
        title = group_title(row, cites)
        if title is not None:
            group = title
            continue
        cells = [clean(c, cites) for c in split_cells(row)]
        rows.append(([group] if grouped else []) + cells)
    return rows


def write_csv(path: Path, header: list, rows: list) -> None:
    bad = [i + 1 for i, r in enumerate(rows) if len(r) != len(header)]
    if bad:
        raise ValueError(f"rows {bad[:10]} do not have {len(header)} cells")
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(buf.getvalue().encode("utf-8"))
    print(f"{path}: {len(rows)} rows x {len(header)} columns")


def read_cites(path) -> dict:
    if not path:
        return {}
    cites = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            key, _, value = line.partition("\t")
            cites[key.strip()] = value.strip()
    return cites


# ----------------------------------------------------------------------------- commands
def cmd_order(paths: list) -> int:
    for path in paths:
        text, pattern = read_any(path)
        order = citation_order(text, pattern)
        print(f"{path}: {len(order)} supplementary tables cited")
        print("  rank\tlabel\tcitations")
        for i, (label, n, _) in enumerate(order, 1):
            print(f"  {i}\t{label}\t{n}")
    return 0


def cmd_table(args) -> int:
    tex = read_tex(args.tex)
    cites = read_cites(args.cites)
    try:
        rows = extract(tex, args.label, cites, bool(args.group_column))
        if args.header:
            header = next(csv.reader([args.header]))
        else:
            width = max(len(r) for r in rows) - bool(args.group_column)
            header = [f"Column {i + 1}" for i in range(width)]
        if args.group_column:
            header = [args.group_column] + header
        write_csv(args.out, header, rows)
    except ValueError as err:
        print(f"FAIL: {err}", file=sys.stderr)
        return 1
    return 0


SAMPLE_TEX = r"""
\section{Methods}
Training settings are in Supplementary Table~\ref{tab:hparams}. % Supplementary Table~\ref{tab:old}
Datasets and licenses are listed in Supplementary Table~\ref{tab:data}; settings again in
Supplementary Table~\ref{tab:hparams}.
\begin{table}
\caption{Hyperparameters.}\label{tab:hparams}
\begin{tabular}{lll}
\toprule
Setting & Value & Reason \\
\midrule
\multicolumn{3}{l}{\textbf{Optimizer}} \\
Learning rate & $3\times10^{-4}$ & best of 3 on the validation fold \\
Weight decay & 0.05 & as in the base recipe~\citep{doe2021base} \\
\multicolumn{3}{l}{\textbf{Data}} \\
Crop size & 224~px & matches the encoder input \\
\bottomrule
\end{tabular}
\end{table}
"""


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / "main.tex").write_text(SAMPLE_TEX, encoding="utf-8")
        (t / "cites.tsv").write_text("doe2021base\tDoe et al. 2021; arXiv 0000.00000\n", encoding="utf-8")
        order = citation_order(read_tex(t / "main.tex"), TEX_CITE)
        assert [(k, n) for k, n, _ in order] == [("tab:hparams", 2), ("tab:data", 1)], order
        doc = ('<w:document><w:body><w:p><w:r><w:t>See Supplementary Table 2 and</w:t></w:r></w:p>'
               '<w:p><w:r><w:t>Supplementary Table 1, then Supplementary Table 2 &amp; more.</w:t></w:r></w:p>'
               '</w:body></w:document>')
        with zipfile.ZipFile(t / "ms.docx", "w") as z:
            z.writestr("word/document.xml", doc)
        text, pat = read_any(t / "ms.docx")
        assert [(k, n) for k, n, _ in citation_order(text, pat)] == [("2", 2), ("1", 1)]
        ns = argparse.Namespace(tex=t / "main.tex", label="tab:hparams", cites=t / "cites.tsv",
                                header="Setting,Value,Reason", group_column="Group", out=t / "a.csv")
        assert cmd_table(ns) == 0
        first = (t / "a.csv").read_bytes()
        assert cmd_table(ns) == 0 and (t / "a.csv").read_bytes() == first, "rerun not byte-identical"
        rows = list(csv.reader(io.StringIO(first.decode("utf-8"))))
        assert rows[0] == ["Group", "Setting", "Value", "Reason"]
        assert rows[1] == ["Optimizer", "Learning rate", "3 \u00d7 10^-4", "best of 3 on the validation fold"], rows[1]
        assert rows[2][3] == "as in the base recipe (Doe et al. 2021; arXiv 0000.00000)", rows[2]
        assert rows[3][:2] == ["Data", "Crop size"] and len(rows) == 4
        ns.cites = None
        assert cmd_table(ns) == 1, "a missing citation key must fail"
    print("self-test passed")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--self-test", action="store_true", help="run on a small synthetic manuscript")
    sub = ap.add_subparsers(dest="cmd")
    o = sub.add_parser("order", help="supplementary tables in order of first citation")
    o.add_argument("paths", nargs="+", type=Path, help=".tex, .docx or text files")
    tb = sub.add_parser("table", help="one labeled LaTeX table to CSV")
    tb.add_argument("tex", type=Path)
    tb.add_argument("--label", required=True, help="the \\label of the table, e.g. tab:hyperparameters")
    tb.add_argument("--out", required=True, type=Path)
    tb.add_argument("--header", help="comma-separated column names (default Column 1, Column 2, ...)")
    tb.add_argument("--group-column", help="name of a first column filled from \\multicolumn group rows")
    tb.add_argument("--cites", type=Path, help="TSV: citation key, then author-year plus accession")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.cmd == "order":
        return cmd_order(args.paths)
    if args.cmd == "table":
        return cmd_table(args)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
