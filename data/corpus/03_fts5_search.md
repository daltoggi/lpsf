# SQLite FTS5 for Text Search

FTS5 is SQLite's built-in full-text search module. It tokenizes text columns
into an inverted index and supports BM25 ranking, phrase queries, prefix
matching, and custom tokenizers. Because it lives inside SQLite, you get
text search and structured queries in the same connection without any
external service.

A typical schema declares a virtual table with the columns to index:
`CREATE VIRTUAL TABLE notes USING fts5(title, body, tokenize='porter unicode61')`.
Inserts go through the virtual table; the underlying index is maintained
automatically. The `MATCH` operator runs queries, and the `bm25()` function
returns ranking scores.

FTS5's BM25 implementation returns smaller (more negative) values for better
matches, which is the opposite convention from many search engines. Most
applications wrap it in `ORDER BY bm25(notes) ASC LIMIT N` and call it a day.

For larger corpora, FTS5 scales acceptably to tens of millions of rows. It
isn't a replacement for Elasticsearch in heavy-write streaming scenarios,
but for local-first apps with a curated corpus it is essentially free —
no extra process, no extra format, no extra failure mode.

Combine FTS5 with structured columns for hybrid filters: full-text match
plus author, date range, tags. The query planner handles the join.
