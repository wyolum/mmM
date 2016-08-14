import sqlite3 as lite
import datetime

con = lite.connect('blood_pressure.db')
cur = con.cursor()

N_TABLE = 4

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

def add_patient(sex, name, birthday):
    sid = sexes[sex]
    birth = str(birthday).split()[0]
    sql = 'INSERT INTO User VALUES(%d, "%s", "%s")' % (sid, name, birth)
    cur.execute(sql)
    con.commit()

def str2ymd(s):
    year, month, day = s.split('-')
    year = int(year)
    month = int(month)
    day = int(month)
    return year, month, day

def add_result(name, sys, dia, day):
    day = str(day)
    sql = 'INSERT INTO BP VALUES("%s", %d, %d, "%s")' % (name, sys, dia, day)
    cur.execute(sql)
    con.commit()

def getAge(name):
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

def getBPs(name):
    sql = 'SELECT sys, dia, day FROM BP WHERE name="%s"' % name
    cur.execute(sql)
    out = cur.fetchall()[0]
    day = out[2]
    # year, month, day = str2ymd(day)
    # day = datetime.date(year, month, day)
    return {'sys': out[0],
            'dia': out[1],
            'day': day}

def getNames():
    sql = 'SELECT name FROM User'
    cur.execute(sql)
    return [l[0] for l in cur.fetchall()]
def test():
    create_tables()
    add_patient('male', 'username', datetime.datetime(1970, 3, 10))
    add_result('username', 110, 70, datetime.datetime.now())
    print getAge('username')
    print getBPs('username')

# test()
