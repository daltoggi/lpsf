# PostgreSQL for Multi-Tenant Services

PostgreSQL is the reasonable default for a backend service that needs
concurrent writes, row-level security, complex queries, and the ability to
scale read replicas independently. It supports MVCC so readers don't block
writers; it has rich indexing options including GIN, GiST, and BRIN; and the
type system covers JSON, arrays, ranges, and full-text search.

The cost is operational. You need a process to run, a network port to manage,
authentication to configure, and backups to schedule. For small applications
this overhead often exceeds the value PostgreSQL adds.

Where Postgres really pays back is in multi-tenant workloads. Row-level
security, partitioning, and connection pooling let one Postgres cluster
serve many customers with strong isolation. Logical replication enables
near-zero-downtime migrations and read scaling. Extensions like pg_trgm
provide trigram indexes for fuzzy text matching that beat naive LIKE queries
by orders of magnitude.

For analytical workloads, materialized views and parallel query support a
wide range of cases short of full-blown OLAP systems. The recent additions
of native parallelism in the planner have made it usable for surprisingly
large datasets.

Reach for Postgres when concurrent writers, network access, or multi-tenant
isolation are core requirements.
