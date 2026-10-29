"""Write government.json and GOVERNMENT.md from hawaii.db. Every box and arrow carries its citation.

Usage: python3 map/render.py [path/to/hawaii.db]
"""
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
DB = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / "data" / "hawaii.db"


def mid(s):
    return s.replace(".", "_").replace("-", "_").replace(":", "_")


def label(s):
    return s.replace('"', "'")


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    bodies = {r["id"]: dict(r) for r in con.execute("select * from body")}
    links = [dict(r) for r in con.execute("select * from link")]
    access = [dict(r) for r in con.execute("select * from access_rule")]
    spine = {k: v for k, v in bodies.items() if v["origin"] == "spine"}
    kids = defaultdict(list)
    for b in bodies.values():
        kids[b["parent_id"]].append(b)

    (HERE / "government.json").write_text(json.dumps(
        {"bodies": sorted(bodies.values(), key=lambda b: b["id"]), "links": links, "access": access},
        indent=1, ensure_ascii=False) + "\n")

    def cite(b):
        mark = "" if b["verified"] else " ✗"
        if not b.get("basis_cite"):
            return ""
        return f"[{b['basis_cite']}]({b['source_url']}){mark}" if b.get("source_url") else b["basis_cite"] + mark

    L = []
    w = L.append
    w("# Government of Hawaii: the map\n")
    w("Generated from the law itself by `map/render.py`. Every box below is created by a specific provision of the "
      "Hawaii Constitution, the Hawaii Revised Statutes, the U.S. Constitution, or the U.S. Code. The build checks "
      "that the quoted words appear in that provision's text. A ✗ means they did not.\n")
    n_spine = len(spine)
    n_ver = sum(1 for b in spine.values() if b["verified"])
    n_mined = sum(1 for b in bodies.values() if b["origin"] == "mined")
    w(f"- {n_spine} structural parts, {n_ver} verified against the text")
    w(f"- {n_mined} boards, commissions, offices, programs and funds found by reading the HRS for the words that "
      "create them ([bodies_mined.csv](bodies_mined.csv)); each keeps the sentence it came from")
    w(f"- {len(links)} connections (supervision, appointment, appeals), each with its citation\n")

    # 1. From the people outward
    w("## 1. From the people outward\n")
    w("```mermaid\nflowchart TB")
    order = ["people.hi", "hi", "hi.leg", "hi.exec", "hi.jud", "hi.oha", "co", "us", "us.congress", "us.president", "us.jud"]
    for i in order:
        if i in bodies:
            w(f'  {mid(i)}["{label(bodies[i]["name"])}"]')
    for i in order:
        b = bodies.get(i)
        if b and b["parent_id"] in order:
            w(f"  {mid(b['parent_id'])} --> {mid(i)}")
    w("  hi -. state of .-> us")
    for c in kids["co"]:
        if c["kind"] == "county":
            w(f'  {mid(c["id"])}["{label(c["name"])}"]')
            w(f"  co --> {mid(c['id'])}")
    w("```\n")
    w("| Part | Created by | The law's words |\n|---|---|---|")
    for i in order + [c["id"] for c in kids["co"]]:
        b = bodies.get(i)
        if b:
            w(f"| {b['name']} | {cite(b)} | “{b['basis_quote']}” |")
    w("")

    # 2. Legislature
    w("## 2. Legislature\n")
    w("| Part | Created by | The law's words |\n|---|---|---|")
    for b in sorted(kids["hi.leg"], key=lambda b: b["name"]):
        if b["origin"] == "spine":
            w(f"| {b['name']} | {cite(b)} | “{b['basis_quote']}” |")
    w("")

    # 3. Executive
    w("## 3. Executive: the governor and the principal departments\n")
    w("HRS § 26-4 lists the principal departments. Each one is created, and its head named, by its own section.\n")
    depts = sorted([b for b in bodies.values() if b["kind"] == "department" and b["level"] == "state"],
                   key=lambda b: b["name"])
    w("```mermaid\nflowchart LR")
    w('  gov["Governor"] --> depts["Principal departments"]')
    for d in depts:
        w(f'  depts --> {mid(d["id"])}["{label(d["name"])}"]')
    w("```\n")
    w("| Department | Created by | Headed by | Attached bodies found in HRS |\n|---|---|---|---:|")
    for d in depts:
        head = next((k for k in kids[d["id"]] if k["kind"] == "head"), None)
        attached = [k for k in kids[d["id"]] if k["origin"] == "mined"]
        w(f"| {d['name']} | {cite(d)} | {head['name'] if head else ''} | {len(attached)} |")
    w("")
    others = [b for b in spine.values() if b["branch"] in ("executive", "independent") and b["kind"] not in ("department", "head", "group")
              and b["level"] == "state" and b["id"] not in ("hi.exec",)]
    w("Other executive and independent bodies:\n")
    w("| Body | Part of | Created by | The law's words |\n|---|---|---|---|")
    for b in sorted(others, key=lambda b: b["name"]):
        parent = bodies.get(b["parent_id"], {}).get("name", "")
        w(f"| {b['name']} | {parent} | {cite(b)} | “{b['basis_quote']}” |")
    w("")

    # 4. Courts and appeal routes
    w("## 4. Courts, and where a decision goes next\n")
    court_ids = [i for i, b in bodies.items() if b["kind"] == "court"] + ["hi.exec.depts"]
    w("```mermaid\nflowchart TB")
    for i in court_ids:
        name = "State agencies (contested cases)" if i == "hi.exec.depts" else bodies[i]["name"]
        w(f'  {mid(i)}["{label(name)}"]')
    for l in links:
        if l["relation"] in ("appeals_to", "certiorari_to", "transfer_to", "contested_case_review_in") and l["from_id"] in court_ids:
            w(f'  {mid(l["from_id"])} -- "{l["relation"].replace("_", " ")}<br/>{label(l["basis_cite"])}" --> {mid(l["to_id"])}')
    for i in court_ids:
        b = bodies.get(i)
        if b and b["parent_id"] in court_ids:
            w(f"  {mid(b['parent_id'])} -. division .-> {mid(i)}")
    w("```\n")
    w("| Court | Created by | The law's words |\n|---|---|---|")
    for i in court_ids:
        if i != "hi.exec.depts":
            b = bodies[i]
            w(f"| {b['name']} | {cite(b)} | “{b['basis_quote']}” |")
    w("")
    w("| From | Goes to | How | Law | The law's words |\n|---|---|---|---|---|")
    for l in links:
        if l["relation"] in ("appeals_to", "certiorari_to", "transfer_to", "contested_case_review_in"):
            w(f"| {bodies[l['from_id']]['name']} | {bodies[l['to_id']]['name']} | {l['relation'].replace('_', ' ')} | "
              f"{l['basis_cite']}{'' if l['verified'] else ' ✗'} | “{l['basis_quote']}” |")
    w("")

    # 5. Public access
    w("## 5. The laws that open records and meetings to the public\n")
    w("| What | Who administers | Law | The law's words |\n|---|---|---|---|")
    for a in access:
        w(f"| {a['record_kind']} | {bodies.get(a['body_id'], {}).get('name', '')} | {a['basis_cite']}"
          f"{'' if a['verified'] else ' ✗'} | “{a['basis_quote']}” |")
    w("")

    # 6. Federal
    w("## 6. Federal government as it reaches Hawaii\n")
    w("| Part | Created by | The law's words |\n|---|---|---|")
    for b in sorted([b for b in bodies.values() if b["level"] == "federal"], key=lambda b: (b["kind"] != "branch", b["name"])):
        w(f"| {b['name']} | {cite(b)} | “{b['basis_quote']}” |")
    w("")

    # 7. Attached bodies
    w("## 7. Boards, commissions, offices, programs and funds attached to departments\n")
    w("Found by reading every in-force HRS section for the words that create a body (\"There is established within "
      "the department of … \", \"… is placed within the department of … for administrative purposes\"). Where the "
      "law does not name a department, the body is listed under *Not stated in the creating sentence*.\n")
    by_parent = defaultdict(list)
    for b in bodies.values():
        if b["origin"] == "mined":
            by_parent[b["parent_id"]].append(b)
    for pid in sorted(by_parent, key=lambda p: (p is None, bodies.get(p, {}).get("name", ""))):
        title = bodies[pid]["name"] if pid else "Not stated in the creating sentence"
        rows = sorted(by_parent[pid], key=lambda b: (b["kind"], b["name"]))
        w(f"<details><summary>{title} ({len(rows)})</summary>\n")
        w("| Name | Kind | Created by |\n|---|---|---|")
        for b in rows:
            w(f"| {b['name']} | {b['kind']} | {cite(b)} |")
        w("\n</details>\n")

    (HERE / "GOVERNMENT.md").write_text("\n".join(L))
    print(f"wrote {HERE / 'GOVERNMENT.md'} and government.json ({len(bodies)} bodies, {len(links)} links)")


if __name__ == "__main__":
    main()
