from flask import Flask, request, render_template, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 用於會話管理，請替換為你的秘密金鑰

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
            self.close()  # 確保關閉連接

    def executeSql(self, sql, data=None):
        """執行插入、更新或刪除語句"""
        self.setServer()
        cursor = self.__server.cursor()
        try:
            cursor.execute(sql, data)
            self.__server.commit()
        finally:
            cursor.close()

    def close(self):
        """關閉資料庫連線"""
        if self.__server and self.__server.is_connected():
            self.__server.close()

# 資料庫連線配置
db_config = {
    'host': "140.131.114.242",
    'port': 3306,
    'dbname': "113-113412",
    'username': "Beauty",
    'pwd': "6Eauty@110460"
}

@app.route('/', methods=["GET"])
def home():
    username = session.get('username')  # 从session中获取用户名
    return render_template('home.html', username=username)

@app.route('/filter', methods=["GET"])
def filter():
    username = session.get('username')  # 从session中获取用户名
    return render_template('filter.html', username=username)

@app.route('/match', methods=["GET"])
def match():
    username = session.get('username')  # 从session中获取用户名
    return render_template('match.html', username=username)  

@app.route('/des', methods=["GET"])
def des():
    username = session.get('username')  # 从session中获取用户名
    return render_template('des.html', username=username)  

@app.route('/login', methods=["GET", "POST"])
def login(): 
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        db = Database(**db_config)
        try:
            sql = "SELECT UserID, Username, Email, Password FROM Users WHERE Email = %s"
            data = (email,)
            results = db.getSqlData(sql, data)

            if results:
                user = results[0]
                user_id, username, user_email, user_password = user
                if check_password_hash(user_password, password):
                    session['user_id'] = user_id
                    session['username'] = username
                    flash('登入成功！', 'success')
                    return redirect(url_for('home'))  # 重定向到主页
                else:
                    flash('密碼錯誤。', 'danger')
            else:
                flash('找不到該電子郵件對應的帳號。', 'danger')
        except mysql.connector.Error as err:
            flash(f"資料庫錯誤: {str(err)}", 'danger')
        finally:
            db.close()
    
    return render_template('login.html')

@app.route('/register', methods=["GET", "POST"])
def register(): 
    if request.method == "POST":
        username = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirmPassword')

        if password != confirm_password:
            flash('密碼與確認密碼不匹配。', 'danger')
            return render_template('register.html')  # 密码不匹配时，返回注册页面

        hashed_password = generate_password_hash(password)

        db = Database(**db_config)
        try:
            sql = "INSERT INTO Users (Username, Email, Password) VALUES (%s, %s, %s)"
            data = (username, email, hashed_password)
            db.executeSql(sql, data)  # 插入用户数据
            flash('註冊成功！請登入。', 'success')  # 添加成功提示
            return redirect(url_for('login'))  # 重定向到登录页面

        except mysql.connector.IntegrityError as ie:
            if ie.errno == 1062:  # 重複鍵錯誤碼
                flash('電子郵件或用戶名已被註冊。', 'danger')
            else:
                flash(f"資料庫錯誤: {str(ie)}", 'danger')
        except mysql.connector.Error as err:
            flash(f"資料庫錯誤: {str(err)}", 'danger')
        finally:
            db.close()

    return render_template('register.html')  # GET请求时，渲染注册页面

@app.route('/logout')
def logout():
    session.clear()
    flash('已成功登出。', 'success')
    return redirect(url_for('home'))

@app.route('/profile', methods=['GET'])
def profile():
    user_id = session.get('user_id')  # 获取登录用户的 ID
    if not user_id:
        flash('請先登入。', 'warning')  # 如果未登录，则跳转到登录页面
        return redirect(url_for('login'))

    db = Database(**db_config)
    
    try:
        # 从数据库中获取用户信息
        sql = "SELECT Username, Email FROM Users WHERE UserID = %s"
        data = (user_id,)
        results = db.getSqlData(sql, data)
        
        if results:
            user = results[0]
            username = user[0]  # 用户名
            email = user[1]     # 邮箱
            
            # 将用户信息传递给模板进行渲染
            return render_template('profile.html', username=username, email=email)
        else:
            flash('找不到用戶資料。', 'danger')
            return redirect(url_for('home'))
    except mysql.connector.Error as err:
        flash(f"資料庫錯誤: {str(err)}", 'danger')
        return redirect(url_for('home'))
    finally:
        db.close()



@app.route('/sun', methods=["GET"])
def sun(): 
    username = session.get('username')  # 从session中获取用户名
    return render_template('sun.html', username=username)  

@app.route('/liquid', methods=["GET"])
def liquid(): 
    username = session.get('username')  # 从session中获取用户名
    return render_template('liquid.html', username=username)  

@app.route('/cookie', methods=["GET"])
def cookie(): 
    username = session.get('username')  # 从session中获取用户名
    return render_template('cookie.html', username=username)  

@app.route('/products', methods=['GET'])  #搜尋欄
def get_products():
    keyword = request.args.get('keyword')
    print(f"Keyword received: {keyword}")  # 測試用
    db = Database(**db_config)
    
    try:
        sql = "SELECT * FROM Products WHERE name LIKE %s"  # 指定資料表
        data = (f"%{keyword}%",)
        results = db.getSqlData(sql, data)
        
        products = [{'id': row[0], 'brand': row[1], 'name': row[2], 'category': row[3], 'sizeprice': row[4], 'des': row[5], 'img': row[6]} for row in results]  # 假設第一列是 id，第二列是 name
        
        return render_template('search.html', products=products, keyword=keyword, username=session.get('username'))  # 傳遞關鍵字到模板
    except mysql.connector.Error as err:
        return f"Error: {str(err)}", 500
    finally:
        db.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # 在所有可用 IP 上運行
