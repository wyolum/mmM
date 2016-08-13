import sqlite3 as lite
import datetime

con = lite.connect('blood_pressure.db')
cur = con.cursor()

N_TABLE = 2

def create_tables():
    sqls = ['DROP TABLE IF EXISTS Sex',
            'DROP TABLE IF EXISTS Patient',
            'DROP TABLE IF EXISTS BP',
            'CREATE TABLE Sex(sex TEXT)',
            'INSERT INTO Sex VALUES ("male")',
            'INSERT INTO Sex VALUES ("female")',
            'INSERT INTO Sex VALUES ("other")',
            'CREATE TABLE Patient(sexid INT, user TEXT, birth DATE)',
            'CREATE UNIQUE INDEX unq_patient ON Patient(user)',
            'CREATE TABLE BP(user TEXT, sys INT, dia INT, day DATE)'
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

def add_patient(sex, user, birthday):
    sid = sexes[sex]
    birth = str(birthday).split()[0]
    sql = 'INSERT INTO Patient VALUES(%d, "%s", "%s")' % (sid, user, birth)
    cur.execute(sql)
    con.commit()

def str2ymd(s):
    year, month, day = s.split('-')
    year = int(year)
    month = int(month)
    day = int(month)
    return year, month, day

def add_result(user, sys, dia, day):
    day = str(day).split()[0]
    sql = 'INSERT INTO BP VALUES("%s", %d, %d, "%s")' % (user, sys, dia, day)
    cur.execute(sql)
    con.commit()

def getAge(user):
    sql = 'SELECT birth FROM Patient WHERE user="%s"' % user
    cur.execute('SELECT * FROM Patient')
    cur.execute(sql)
    result = cur.fetchall()
    if len(result) == 0:
        raise ValueError("User %s, not found" % user)
    elif len(result) == 1:
        birth = result[0][0]
        year, month, day = str2ymd(birth)
        birth = datetime.datetime(year, month, day)
    else:
        raise ValueError("Duplicate user %s" % user)
        
    now = datetime.datetime.now()
    return (now - birth).days / 365.25

def getBPs(user):
    sql = 'SELECT sys, dia, day FROM BP WHERE user="%s"' % user
    cur.execute(sql)
    out = cur.fetchall()[0]
    day = out[2]
    year, month, day = str2ymd(day)
    day = datetime.date(year, month, day)
    return {'sys': out[0],
            'dia': out[1],
            'day': day}

def test():
    create_tables()
    add_patient('male', 'justin', datetime.datetime(1970, 3, 10))
    add_result('justin', 110, 70, datetime.datetime.now())
    print getAge('justin')
    print getBPs('justin')
# test()
