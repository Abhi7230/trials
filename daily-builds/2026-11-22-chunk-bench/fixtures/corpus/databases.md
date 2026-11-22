# Database Systems

## Relational Databases

### SQL Fundamentals

Structured Query Language (SQL) is used to manage relational databases. Basic operations include:

**SELECT**: Retrieve data from tables
```sql
SELECT name, email FROM users WHERE age > 18;
```

**INSERT**: Add new records
```sql
INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com');
```

**UPDATE**: Modify existing records
```sql
UPDATE users SET email = 'newemail@example.com' WHERE id = 1;
```

**DELETE**: Remove records
```sql
DELETE FROM users WHERE inactive = true;
```

### Normalization

Database normalization organizes data to reduce redundancy:

**First Normal Form (1NF)**: Eliminate repeating groups
**Second Normal Form (2NF)**: Remove partial dependencies
**Third Normal Form (3NF)**: Eliminate transitive dependencies

Proper normalization improves data integrity and reduces storage but may require more joins.

### Indexes

Indexes speed up data retrieval by creating sorted data structures. Types include:
- B-tree indexes: Default for most databases
- Hash indexes: Fast equality lookups
- Full-text indexes: Text search capabilities
- Composite indexes: Multiple columns

Trade-off: Indexes improve read performance but slow down writes.

## Transactions and ACID

### ACID Properties

**Atomicity**: Transactions complete fully or not at all
**Consistency**: Database remains in valid state
**Isolation**: Concurrent transactions don't interfere
**Durability**: Committed changes persist

### Transaction Isolation Levels

- Read Uncommitted: Allows dirty reads
- Read Committed: Prevents dirty reads
- Repeatable Read: Prevents non-repeatable reads
- Serializable: Full isolation, prevents phantom reads

## NoSQL Databases

### Document Stores

MongoDB and CouchDB store data as JSON-like documents. Flexible schemas allow easy iteration.

### Key-Value Stores

Redis and DynamoDB provide fast lookups with simple key-value pairs. Ideal for caching and session storage.

### Column-Family Stores

Cassandra and HBase organize data by columns rather than rows. Optimized for write-heavy workloads and time-series data.

### Graph Databases

Neo4j and Amazon Neptune excel at relationship-heavy data. Use cases include social networks, recommendation engines, and fraud detection.

## Query Optimization

Optimization techniques:
- Use appropriate indexes
- Avoid SELECT *
- Minimize subqueries
- Use prepared statements
- Analyze query execution plans
- Partition large tables
- Cache frequent queries

EXPLAIN command shows how database executes queries, helping identify bottlenecks.
