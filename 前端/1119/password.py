from flask import Flask, render_template, request, redirect, url_for, flash
import hashlib
import mysql.connector
import secrets

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 用於 flash 消息

# 你的 Database 連接類如前面所述
class Database:
    def __init__(self, host, port, dbname, username, pwd):
        self.host = host
        self.port = port
        self.database = dbname
        self.user = username
        self.password = pwd
        self.__server = None

    @property
    def Server(self):
        return self.__server
    
    @Server.setter
    def Server(self, value):
        self.__server = value

    def setServer(self):
        """建立資料庫連線，如果尚未連接或連接已失效"""
        if self.Server is None or not self.Server.is_connected():
            self.Server = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )

    def test(self):
        """測試資料庫是否成功連接"""
        self.setServer()
        return self.Server.is_connected()

# 路由：忘記密碼頁面
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        db = Database("140.131.114.242", 3306, "113-113412", "Beauty", "6Eauty@110460")
        db.setServer()

        cursor = db.Server.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user:
            token = secrets.token_urlsafe(16)  # 生成隨機的 token
            reset_link = url_for('reset_password', token=token, _external=True)
            
            # 可以發送重設密碼連結給用戶（這裡假設你有郵件系統）
            flash(f'已發送重設密碼的連結到 {email}。', 'info')

            # 保存 token 以便用於重設密碼
            cursor.execute("UPDATE users SET reset_token = %s WHERE email = %s", (token, email))
            db.Server.commit()
        else:
            flash('該電子郵件尚未註冊。', 'error')

    return render_template('forgot_password.html')

# 路由：重設密碼
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    db = Database("140.131.114.242", 3306, "113-113412", "Beauty", "6Eauty@110460")
    db.setServer()

    cursor = db.Server.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE reset_token = %s", (token,))
    user = cursor.fetchone()

    if not user:
        flash('重設密碼連結無效或已過期。', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        hashed_password = hashlib.sha256(new_password.encode()).hexdigest()  # 使用 SHA-256 哈希密碼

        # 更新資料庫中的密碼
        cursor.execute("UPDATE users SET password = %s, reset_token = NULL WHERE reset_token = %s", (hashed_password, token))
        db.Server.commit()

        flash('密碼已成功更新，請重新登入。', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html')

if __name__ == '__main__':
    app.run(debug=True)
