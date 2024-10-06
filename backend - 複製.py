from flask import Flask, request, render_template
import mysql.connector

class Database:
    def __init__(self, host, port, dbname, username, pwd):
        self.host = host
        self.port = port
        self.database = dbname
        self.user = username
        self.password = pwd
        self.__server = None

    def setServer(self):
        """建立資料庫連線，如果尚未連接或連接已失效"""
        if self.__server is None or not self.__server.is_connected():
            self.__server = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )

    def getSqlData(self, sql, data=None):
        """執行查詢並返回結果集"""
        self.setServer()
        cursor = self.__server.cursor()
        try:
            cursor.execute(sql, data)
            return cursor.fetchall()  # 返回查詢結果
        finally:
            cursor.close()

    def close(self):
        """關閉資料庫連線"""
        if self.__server and self.__server.is_connected():
            self.__server.close()

app = Flask(__name__)

@app.route('/', methods=["GET"])
def home():
    return render_template('home.html')  # 傳遞關鍵字到模板

@app.route('/filter', methods=["GET"]) # 篩選
def filter():
    return render_template('filter.html') 

@app.route('/match', methods=["GET"])  #匹配度
def match():
    return render_template('match.html')  

@app.route('/des', methods=["GET"])  #產品詳情
def des():
    return render_template('des.html')  

@app.route('/login', methods=["GET"]) #登入
def login(): 
    return render_template('login.html')  

@app.route('/register', methods=["GET"]) #註冊
def register(): 
    return render_template('register.html')  

@app.route('/sun', methods=["GET"]) #防曬分類
def sun(): 
    return render_template('sun.html')  

@app.route('/liquid', methods=["GET"]) #粉地一分類
def liquid(): 
    return render_template('liquid.html')  

@app.route('/cookie', methods=["GET"]) #粉餅分類
def cookie(): 
    return render_template('cookie.html')  

@app.route('/products', methods=['GET'])  #搜尋欄
def get_products():
    keyword = request.args.get('keyword')
    print(f"Keyword received: {keyword}")  # 測試用
    db = Database(host="140.131.114.242", port=3306, dbname="113-113412", username="Beauty", pwd="6Eauty@110460")
    
    try:
        sql = "SELECT * FROM Products WHERE name LIKE %s"  # 指定資料表
        data = (f"%{keyword}%",)
        results = db.getSqlData(sql, data)
        
        products = [{'id': row[0], 'brand': row[1], 'name': row[2], 'category': row[3], 'sizeprice': row[4], 'des': row[5], 'img': row[6]} for row in results]  # 假設第一列是 id，第二列是 name
        
        return render_template('search.html', products=products, keyword=keyword)  # 傳遞關鍵字到模板
    except mysql.connector.Error as err:
        return f"Error: {str(err)}", 500
    finally:
        db.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # 在所有可用 IP 上運行


