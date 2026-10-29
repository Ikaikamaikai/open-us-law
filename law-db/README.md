# law-db: a fixed copy of the law, as data files

One folder per version. Each version is kept unchanged. A new version gets a new folder.

| Version | Sections | Files |
|---|---|---|
| `v2026.10` | 326,549 | 58 Parquet files: one each for HRS, HAR, Hawaii constitution, Hawaii court rules, Hawaii AG opinions, Hawaii agency guidance, U.S. Code, U.S. Constitution, federal court rules; one per CFR title (Title 35 is not included) |

`manifest.json` in each folder gives every file's row count, size and sha256, and lists the source files it was made from.

- **Made by:** `portal/export_law_db.py` in the HAWAIIPUBLICINFO repository. Before the manifest is written, every row is checked against the source CSVs, by section id and sha256 of the text.
- **Used by:** the Hawaii Public Information Archive (`portal/build.py`). It reads the law from here instead of keeping its own copy.
- **Sources:** Open US Law snapshot v2026.09.1 (vaquill.ai), licensed CC BY-NC 4.0, for non-commercial use with attribution. The CFR text comes from the govinfo eCFR bulk XML.

Read it with any Parquet tool. For example, with DuckDB:

```sql
SELECT citation, heading FROM read_parquet('law-db/v2026.10/*.parquet') WHERE number = '92F-11';
```
