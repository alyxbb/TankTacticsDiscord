import sqlite3
import logging
logger = logging.getLogger("tankTactics.database")

conn = sqlite3.connect("resources/db.sqlite")
c = conn.cursor()
c.execute("SELECT nickname FROM player")
