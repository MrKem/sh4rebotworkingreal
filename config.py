import sqlite3
db = sqlite3.connect('db.db', check_same_thread=False)
sql = db.cursor()

token = '5119897324:AAGAKMX8ezz-YqSzQjoMnAmpRBq0NJBk1eg'

admins = [717778881]

username_bot = 'sh4re_bot'

global link_channel
link_channel = ''