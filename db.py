import sqlite3

def get_db():
    db = sqlite3.connect('db.db')
    db.row_factory = sqlite3.Row

    return db


def close_db(db):
    db.close()


def create_db():
    db = sqlite3.connect('db.db')

    with open('schema.sql') as f:
        db.executescript(f.read())

    db.commit()
    db.close()

if __name__=='__main__':
    create_db()