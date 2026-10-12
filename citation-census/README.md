# US Legal Citation Census

Every non-case legal citation that appears in 10,745,929 US court opinions, with how often it is cited.
Statutes, the U.S. Code, regulations, court rules (federal, state and local), constitutions, session laws and administrative registers.
Case citations (U.S., F.2d, So. 2d and the rest), treatises and Westlaw or Lexis cites are not included.

**2,775,821 distinct citations, 34,774,058 occurrences, in 331 CSV files.**

## Layout

```
citations/<category>/<jurisdiction>.csv     most-cited first; files over 250,000 rows are split as <jurisdiction>-001.csv, -002.csv
stats/by_type.csv  stats/by_jurisdiction.csv  stats/summary.json
stats/top_cited/<category>.csv               the 1,000 most-cited citations per category
samples/<category>.csv                       100 random rows per category, to look at before downloading
MANIFEST.json  SHA256SUMS                    every file with its row count, size and checksum
```

Categories: `statutes`, `court-rules`, `regulations`, `constitutions`, `administrative-registers`, `session-laws`.
Jurisdiction files use the two-letter state code in lower case, `federal` for U.S.-level law, and `unknown` where neither the citation nor the court says.

## Columns

| column | meaning |
| --- | --- |
| `citation` | normalised citation, pinpoints removed (`18 U.S.C. § 1956`, not `18 U.S.C. § 1956(a)(1)(B)`) |
| `citation_key` | the citation lower-cased with spacing collapsed. Variants that differ only in case or spacing (`Tex. Fam. Code Ann. § 161.001` and `TEX. FAM. CODE ANN. § 161.001`) are separate rows; group by this key to merge them. `opinions` and `courts` cannot be summed across variants |
| `type` | Statute, Court Rule, Regulation, Constitution, Session Law or Admin. Register |
| `subtype` | for example `usc`, `cfr`, `federal_rule`, `local_rule`, `state_statute`, `state_regulation`, `federal_register` |
| `jurisdiction` | two-letter code or `US`. A guess: taken from the citation when it names a jurisdiction, otherwise from the deciding court's state |
| `occurrences` | times the citation appears across all opinions |
| `opinions` | distinct opinions that cite it |
| `courts` | distinct courts whose opinions cite it |
| `first_year`, `last_year` | earliest and latest decision year citing it |
| `resolved` | `true` if Vaquill's citation resolver returned a section for it (run 2026-10-10; rows rewritten in the 2026-10-12 cleaning were resolved on that date) |
| `answer_kind` | `exact`, `container` (a chapter or rule group), `multiple` (a range or several candidates), `repaired` (a known miscitation corrected), `register_reference`, or `unresolved` |

`resolved` describes our resolver at one date and is not a statement about the law.
`unresolved` includes law we do not hold, repealed or renumbered law, old numbering, malformed citations and extraction errors.
Internal section identifiers and source URLs are deliberately not published.

## What is and is not in it

- The extractor flags each citation `strong` or weak. Only strong ones are published: 496,867 weak fragments, 2,344 known artifacts such as court docket headers, and 23 strings that carried a publisher parenthetical, a database cite or a URL were left out.
- Extraction is not perfect. Expect roughly 80 to 85 percent recall and 92 to 98 percent precision on unseen text.
  It misses a bare `§ 1983` with no code named, rules cited without their set, and named acts with no code.
  Strings that are not citations to law (bill numbers, treatises, docket entries, case reporters) were removed in the 2026-10-12 cleaning below; a few that look like codes may remain.
- The jurisdiction column is a guess for citations that do not name one.
- No opinion text, parties, judges or opinion identifiers are included, only citation strings and counts.

## Source

Opinions come from CourtListener, a project of Free Law Project, read through a self-hosted mirror.
Extractor version 0.6.0, built 2026-10-10.

## Licence and attribution

This folder does not carry a data licence of its own yet. The repository `LICENSE` (Apache-2.0) covers the code.
The opinions behind these counts come from CourtListener, a project of Free Law Project. Please attribute: "Derived from CourtListener, a project of Free Law Project".

## Cleaning (2026-10-12)

A resolver pass on 2026-10-10 left about 1.6 million rows unresolved.
Part of that is noise that was never a citation to law, and part is a real citation the extractor mangled.
Only rows that did NOT resolve were ever touched. A row the resolver answers is a real citation and is never removed or rewritten.

### Removed

- bill numbers and legislative history (`H.R. 1234`, `S.B. 567 § 2`, committee reports, `Cong. Rec.`): 2,382 rows, 4,921 occurrences.
- case reporters typed as rules or regulations (Tex. Crim. Reports, Puerto Rico Reports, Military Justice Reporter and Court-Martial cites, N.J. Misc. Reports, Kentucky Law Reporter): 55,743 rows, 161,571 occurrences.
- docket and record cites (`ECF No. 12 § 3`, `D.I.`, `J.A.`, exhibits, transcripts, `SMF § 49`, `DSEIS § 2.1.2`): 7,647 rows, 11,975 occurrences.
- treatises and other secondary sources (Am. Jur., C.J.S., Corpus Juris, Restatements, Wright & Miller, Moore's, state Jur. and practice treatises, A.L.R., law reviews, Fed. Res. Bull. and similar bulletins): 31,108 rows, 54,081 occurrences.

In total 96,880 rows and 232,548 occurrences were removed.
A string that carries a real code AND one of these (for example `54 Wash. L. Rev. 275 (1979). RCW 90.58.140`) is not removed; it is repaired instead when the repair resolves.

### Repaired

A deterministic rewrite is applied only when the rewritten string resolves with the citation resolver (or is already a row the resolver answered): a footnote number glued to the front of a code that takes no title (`9 Fed. R. Civ. P. 8`), a case or law-review citation glued to the front, a digit written as a letter (`25ll` for `2511`), a misspelled code word (`ULS.C.`, `Crv. P.`), glued or doubled punctuation.
78,111 rows were merged into an existing row and 7,404 were rewritten in place.
A merged row sums the occurrences, takes the earliest first year and the latest last year, and takes the larger of the two `opinions` and `courts` values, so those two columns on a merged row are lower bounds.
Rewritten rows were resolved on 2026-10-12 rather than 2026-10-10.

### Changelog

- 2026-10-12: removed 96,880 noise rows, repaired 85,515. The dataset now holds 2,775,821 distinct citations (was 2,950,812) and 34,774,058 occurrences (was 35,006,606).
- 2026-10-10: first release.
