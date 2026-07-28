# Local Persistence Sqlite Policy

AION-224 may use Python standard-library sqlite support only with explicit absolute paths outside the repository, symlink rejection, operator-owned 0700 parent directories, 0600 database files, foreign keys on, WAL mode, FULL synchronous mode, trusted schema off, extension loading disabled, parameterized statements only, and no operator-supplied SQL.
