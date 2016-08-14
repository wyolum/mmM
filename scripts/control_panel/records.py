import sqlite3 as lite
import datetime

filename = 'blood_pressure.db'

con = lite.connect(filename)
cur = con.cursor()

N_TABLE = 3

def create_tables():
    sqls = ['DROP TABLE IF EXISTS Sex',
            'DROP TABLE IF EXISTS User',
            'DROP TABLE IF EXISTS BP',
            'CREATE TABLE Sex(sex TEXT)',
            'INSERT INTO Sex VALUES ("male")',
            'INSERT INTO Sex VALUES ("female")',
            'INSERT INTO Sex VALUES ("other")',
            'CREATE TABLE User(sexid INT, name TEXT, birth DATE)',
            'CREATE UNIQUE INDEX unq_username ON User(name)',
            'INSERT INTO User VALUES(2, "anon", "2000-01-01")',
            'CREATE TABLE BP(name TEXT, sys INT, dia INT, day DATETIME)'
    ]
            
    for sql in sqls:
        cur.execute(sql);
    con.commit()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
if len(cur.fetchall()) != N_TABLE:
    print 'Creating tables'
    create_tables()

cur.execute('SELECT ROWID, sex FROM Sex')
sexes = {}
for id, sex in cur.fetchall():
    sexes[sex] = id

def add_user(sex, name, birthday):
    sid = sexes[sex]
    birth = str(birthday).split()[0]
    sql = 'INSERT INTO User VALUES(%d, "%s", "%s")' % (sid, name.lower(), birth)
    cur.execute(sql)
    con.commit()

def get_users():
    sql = 'SELECT * FROM User'
    cur.execute(sql)
    return cur.fetchall()

def get_lastuser():
    out = 'anon'
    sql = 'SELECT name FROM BP ORDER BY DAY DESC LIMIT 1'
    cur.execute(sql)
    rows = cur.fetchall()
    if len(rows) == 1:
        out = rows[0][0]
    else:
        out = 'anon'
    return out
    
    
def str2ymd(s):
    year, month, day = s.split('-')
    year = int(year)
    month = int(month)
    day = int(month)
    return year, month, day

def add_result(user, sys, dia, day):
    day = str(day)
    sql = 'INSERT INTO BP VALUES("%s", %d, %d, "%s")' % (user, sys, dia, day)
    cur.execute(sql)
    con.commit()

def get_age(name):
    sql = 'SELECT birth FROM User WHERE name="%s"' % name
    cur.execute('SELECT * FROM User')
    cur.execute(sql)
    result = cur.fetchall()
    if len(result) == 0:
        raise ValueError("User %s, not found" % name)
    elif len(result) == 1:
        birth = result[0][0]
        year, month, day = str2ymd(birth)
        birth = datetime.datetime(year, month, day)
    else:
        raise ValueError("Duplicate user name %s" % name)
        
    now = datetime.datetime.now()
    return (now - birth).days / 365.25

def get_BPs(name):
    sql = 'SELECT sys, dia, day FROM BP WHERE name="%s"' % name
    cur.execute(sql)
    out = cur.fetchall()[0]
    day = out[2]
    # year, month, day = str2ymd(day)
    # day = datetime.date(year, month, day)
    return {'sys': out[0],
            'dia': out[1],
            'day': day}

def get_names():
    sql = 'SELECT name FROM User'
    cur.execute(sql)
    return [l[0] for l in cur.fetchall()]
def test():
    if raw_input('This test destroys all data. Continue[n]?') == 'y':
        create_tables()
        add_user('male', 'anon', datetime.datetime(1970, 3, 10))
        add_result('anon', 110, 70, datetime.datetime.now())
        add_user('male', 'justin', datetime.datetime(1970, 3, 10))
        add_result('justin', 110, 70, datetime.datetime.now())
        print get_age('anon')
        print get_BPs('anon')
        print get_users()
        print get_BPs('justin')
        print get_lastuser()
    else:
        print 'Test aborted.'
# test()
