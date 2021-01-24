import sqlite3
import bcrypt


conn = sqlite3.connect("dataBase.db")
f = open("interests.txt", "r")
query = "INSERT INTO `interests` (interest) VALUES (?)"
c = conn.cursor()
for i in f:
    c.execute(query, (i[:-1],))
conn.commit()
conn.close()
