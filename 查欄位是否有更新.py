import mysql.connector

db = mysql.connector.connect(
    host="140.131.114.242",
    port=3306,
    database="113-113412",
    user="Beauty",
    password="6Eauty@110460"
)

cursor = db.cursor()
cursor.execute("SELECT ReviewID, Rating FROM Reviews")
results = cursor.fetchall()

for row in results:
    print(f"ReviewID: {row[0]}, Rating: {row[1]}")

cursor.close()
db.close()
