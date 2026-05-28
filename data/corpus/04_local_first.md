# Local-First Software Design

Local-first software keeps user data on the user's device by default, with
optional sync to remote servers. The phrase comes from the Ink & Switch
research lab. Key properties include fast access to local data, offline
operation, long-term data ownership, and the freedom to choose where data
syncs.

Implementing local-first software typically combines: an embedded database
(SQLite is common), a conflict-free replicated data type or operational
transformation layer for sync, end-to-end encryption for any cloud
intermediary, and a UI that does not assume a network connection.

The hardest design problem is conflict resolution. CRDTs guarantee eventual
consistency for many data shapes without coordination; operational
transformation handles richer document semantics at the cost of needing a
server. Many production apps adopt a hybrid: CRDTs for the data model,
plus server-side reconciliation for things CRDTs can't model well, such as
referential integrity.

The benefit users see is responsiveness and ownership. A local-first app
opens instantly because it doesn't wait for a network round-trip, and a
user's data outlives the company that built the app. The cost is engineering
complexity, especially around schema migration and sync conflict UX.

Treat local-first as a design philosophy, not a single technique.
