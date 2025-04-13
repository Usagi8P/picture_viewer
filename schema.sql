DROP TABLE IF EXISTS files;

CREATE TABLE files(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder TEXT NOT NULL,
    filename TEXT NOT NULL,
    delete_action TEXT CHECK (delete_action in ('keep','delete')),
    rotation INTEGER DEFAULT 0,
    UNIQUE (folder, filename)
);
