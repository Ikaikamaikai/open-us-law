# Usage: python write_column_list.py <output .csv> <us_hi_statutes.parquet> <us_hi_court_rules.parquet> <us_hi_ag_opinion.parquet> <us_hi_guidance.parquet> <us_hi_constitutions.parquet>
import sys, csv, collections, pyarrow.parquet as pq
out, files = sys.argv[1], sys.argv[2:]
labels = {"statutes": "statutes", "court_rules": "court rules", "ag_opinion": "AG opinions", "guidance": "guidance", "constitutions": "constitution"}
tables = {}
for f in files:
    key = f.rsplit("/", 1)[-1].split("-", 1)[-1] if "-us_hi_" in f else f.rsplit("/", 1)[-1]
    key = key.replace("us_hi_", "").replace(".parquet", "")
    tables[key] = pq.read_table(f)
meaning = {
 "act_id": "Vaquill's own ID for the row. The format is theirs, e.g. STATE_HI_D1_T7_C90D_S90D-5.",
 "citation": "Full citation as written for the document.",
 "citation_short": "Shorter form of the citation.",
 "state": "Two-letter state code, lower case.",
 "jurisdiction": "Country code. Every Hawaii row says US, not HI.",
 "document_type": "Kind of document.",
 "title_number": "Title number in the code (statutes only).",
 "title_name": "Name of the collection the row belongs to. For statutes it says HI Code rather than Hawaii Revised Statutes.",
 "chapter": "Chapter number (statutes only).",
 "chapter_name": "Chapter name. Empty in every Hawaii file.",
 "section_number": "Section number, or opinion number for AG opinions.",
 "section_title": "Heading of the section, or subject line of the opinion.",
 "breadcrumb": "Where the row sits in the hierarchy (division, title, chapter, section), stored as text that looks like a list.",
 "display_path": "Same hierarchy as one readable line.",
 "act_status": "Whether the law is in force, repealed, reserved, etc.",
 "text": "The full text of the section or document.",
 "word_count": "Number of words in text.",
 "source_url": "Link to the government page or PDF the text came from.",
 "last_amended_year": "Year the section was last amended, where found.",
 "subsection_count": "How many subsections the section has.",
 "cross_references_usc": "Citations to the US Code found in the text, stored as text that looks like a list.",
 "cross_references_cfr": "Citations to federal regulations (CFR) found in the text, stored as text that looks like a list.",
 "public_laws_referenced": "Federal public laws mentioned in the text, stored as text that looks like a list.",
 "year": "A year. For AG opinions it is the year issued; for statutes it is 2026 on every row, so it reads like the snapshot year.",
 "official_status": "Publisher's own label such as unofficial. Empty in every Hawaii file.",
 "currency_note": "Publisher's statement of how current the text is. Empty in every Hawaii file.",
 "adopting_citations": "What adopted or amended the rule. A real list type, unlike the other list-like columns. Empty in every Hawaii file.",
}
first = next(iter(tables.values()))
ex = tables["statutes"].to_pylist()[len(tables["statutes"]) // 2]
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["column_number", "column_name", "value_type", "what_it_holds", "example_from_hawaii_statutes", "how_often_filled_in_hawaii_files", "source_files", "described_on"])
    for i, (name, ty) in enumerate(zip(first.schema.names, first.schema.types), 1):
        parts = []
        for k, t in tables.items():
            vals = t.column(name).to_pylist()
            filled = sum(1 for v in vals if v not in (None, "", "[]", []))
            pct = round(100*filled/len(vals)); parts.append(f"{labels[k]} " + ("under 1%" if filled and pct == 0 else f"{pct}%"))
        if name == "document_type":
            vals = sorted({v for t in tables.values() for v in t.column(name).to_pylist()})
            what = meaning[name] + " Values in Hawaii files: " + ", ".join(vals) + "."
        elif name == "act_status":
            vals = collections.Counter(v for t in tables.values() for v in t.column(name).to_pylist())
            what = meaning[name] + " Values in Hawaii files: " + ", ".join(f"{k} ({n})" for k, n in vals.most_common()) + "."
        else:
            what = meaning[name]
        e = ex[name]
        e = "" if e is None else str(e)
        if len(e) > 160: e = e[:160] + "..."
        tstr = {"string": "text", "int64": "whole number", "list<element: string>": "list of text"}.get(str(ty), str(ty))
        w.writerow([i, name, tstr, what, e, "; ".join(parts), "us_hi_statutes, us_hi_court_rules, us_hi_ag_opinion, us_hi_guidance, us_hi_constitutions (Open US Law v2026.09.1, uploaded by owner)", "2026-10-18"])
print("wrote", out)
