# SQLite for Application Data

SQLite excels as an embedded database for desktop, mobile, and small-server
applications. A single file holds the entire database; backup is just a copy;
there is no client-server overhead. For workloads where the working set fits
in memory and concurrent writes are rare, SQLite often outperforms heavier
databases by sidestepping IPC and connection-pool latency.

The main caveat is concurrent write throughput. SQLite serializes writes at
the database-file level via its locking protocol. Applications with many
simultaneous writers (or long-running write transactions) will see writer
contention. WAL mode mitigates this for the common case of many readers and
few writers, but it does not turn SQLite into a multi-master system.

For analytical reads at moderate scale, SQLite is surprisingly competitive,
especially with virtual tables and FTS5 for text search. Storing structured
data and a full-text index in the same file simplifies deployment.

When choosing SQLite, consider: working-set size relative to RAM, the
read/write ratio, whether you need network access, and the availability of
client libraries in your language. For local-first apps it is usually the
right default.
