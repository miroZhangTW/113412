from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_cors import CORS
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import jsonify
from utils import simplify_review


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

# 定義一個裝飾器來保護需要登入的路由
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('請先登入。', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=["GET"])
def home():
    username = session.get('username')  # 从session中获取用户名
    
    db = Database(**db_config)
    try:
        # 查詢每個類別的最高分產品
        categories = ['%防曬%', '%粉底液%', '%粉餅%', '%粉底液%']  # 可以根据需要添加其他类别
        highest_rated_products = {}

        for category in categories:
            # 修改查询以包括 ImageURL
            sql = """
                SELECT pa.product_name, pa.product_id, pa.brand_name, pa.avg_rating, p.ImageURL
                FROM ProductAverageRatings pa
                JOIN Products p ON pa.product_name = p.Name  # 连接 Products 表
                WHERE pa.category LIKE %s
                ORDER BY pa.avg_rating DESC
                LIMIT 1
            """
            data = (category,)
            result = db.getSqlData(sql, data)

            if result:
                highest_rated_products[category] = {
                    'product_name': result[0][0],
                    'product_id': result[0][1],
                    'brand_name': result[0][2],
                    'avg_rating': result[0][3],
                    'img': result[0][4]  # 添加 ImageURL
                }

    except mysql.connector.Error as err:
        flash(f"資料庫錯誤: {str(err)}", 'danger')
    finally:
        db.close()

    return render_template('home.html', username=username, highest_rated_products=highest_rated_products)

@app.route('/get_recommendations', methods=['POST'])      # 表單的
def get_recommendations():
    # 假設前端會發送一個 JSON 包含 'result' 字段，例如 {'result': '敏感乾性肌膚'}
    data = request.json
    result = data.get('result', '')

    keywords = []
    if '乾性' in result:
        keywords.append('%乾性%')
    if '油性' in result:
        keywords.append('%油性%')
    if '混合' in result:
        keywords.append('%混合%')

    if not keywords:
        return jsonify({'error': '未匹配到任何膚質類型關鍵字'})

    db = Database(**db_config)
    recommendations = []
    seen_products = set()  # 使用集合來跟蹤已添加的產品
    try:
        # 逐個關鍵字查詢，並篩選 SkinTypeRating 最高的三個產品
        for keyword in keywords:
            sql = """
                SELECT r.brand_name, r.product_name, r.size, r.price, p.ImageURL
                FROM Reviews r
                JOIN Products p ON r.product_name = p.Name  -- 使用名稱進行關聯
                WHERE r.BestSkinType LIKE %s
                ORDER BY r.SkinTypeRating DESC
                LIMIT 3
            """
            data = (keyword,)
            results = db.getSqlData(sql, data)
            
            for row in results:
                product_key = (row[0], row[1], row[2])  # 使用品牌、產品名稱和尺寸作為唯一標識
                if product_key not in seen_products:  # 如果未添加過，則添加到推薦列表
                    seen_products.add(product_key)
                    recommendations.append({
                        'brand_name': row[0], 
                        'product_name': row[1], 
                        'size': row[2], 
                        'price': row[3],
                        'image_url': row[4]  # 新增這一行以獲取 ImageURL
                    })

    except mysql.connector.Error as err:
        return jsonify({'error': str(err)})
    finally:
        db.close()

    # 返回正確的 JSON 數據
    return jsonify({'recommendations': recommendations})


@app.route('/skin_tests_page', methods=['GET'])
@login_required
def skin_tests_page():
    username = session.get('username')
    db = Database(**db_config)

    try:
        sql = "SELECT Sensitivity, Hydration, Oiliness, Result, TestDate FROM SkinTests WHERE Username = %s"
        data = (username,)
        results = db.getSqlData(sql, data)

        skin_tests = [{
            'sensitivity': row[0],
            'hydration': row[1],
            'oiliness': row[2],
            'result': row[3],
            'test_date': row[4]
        } for row in results]

        return render_template('skin_tests.html', skin_tests=skin_tests)
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        db.close()



@app.route('/submit_skin_test', methods=['POST'])
@login_required
def submit_skin_test():
    data = request.get_json()
    sensitivity = data.get('sensitivity')
    hydration = data.get('hydration')
    oiliness = data.get('oiliness')
    result = data.get('result')

    if not all([sensitivity, hydration, oiliness, result]):
        return jsonify({'success': False, 'message': '缺少必要的數據'}), 400

    username = session.get('username')

    db = Database(**db_config)
    try:
        sql = """
            INSERT INTO SkinTests (Username, Sensitivity, Hydration, Oiliness, Result)
            VALUES (%s, %s, %s, %s, %s)
        """
        data = (username, sensitivity, hydration, oiliness, result)
        db.executeSql(sql, data)
        return jsonify({'success': True}), 200
    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': str(err)}), 500
    finally:
        db.close()

@app.route('/filter', methods=["GET"])
def filter():
    username = session.get('username')  # 从session中获取用户名
    return render_template('filter.html', username=username)

@app.route('/match', methods=['GET'])
def match():
    db = Database(**db_config)
    price_range = request.args.get('price', '全部範圍')
    brand_preference = request.args.get('brand', '全部品牌')
    category_preference = request.args.get('category', '全部類別')

    # 構建基礎查詢
    query = """
        SELECT DISTINCT r.brand_name, r.product_name, r.size, r.price, r.category, p.ImageURL, r.SkinTypeRating
        FROM Reviews r
        JOIN Products p ON r.product_name = p.Name
        WHERE 1=1
    """
    filters = []

    # 價格範圍篩選
    if price_range == '1~250元':
        query += " AND (r.price BETWEEN 1 AND 250 OR r.price IS NULL)"
    elif price_range == '251~400元':
        query += " AND (r.price BETWEEN 251 AND 400 OR r.price IS NULL)"
    elif price_range == '401元以上':
        query += " AND (r.price > 400 OR r.price IS NULL)"

    # 品牌偏好篩選
    if brand_preference and brand_preference != '全部品牌':
        query += " AND r.brand_name = %s"
        filters.append(brand_preference)

    # 產品類別篩選
    if category_preference and category_preference != '全部類別':
        if category_preference == '防曬':
            query += " AND (r.category LIKE '%防曬%' OR r.category IS NULL)"
        else:
            query += " AND r.category = %s"
            filters.append(category_preference)

    # 查詢最新的檢測結果
    latest_test_query = """
        SELECT Result
        FROM SkinTests
        WHERE Username = %s
        ORDER BY TestDate DESC
        LIMIT 1
    """

    try:
        # 獲取最新的測驗結果
        username = session.get('username')
        latest_result = None  # 初始化為 None

        if username:
            result = db.getSqlData(latest_test_query, (username,))
            if result:
                latest_result = result[0][0]  # 取得最新測驗結果
            else:
                latest_result = "你還沒測驗膚質喔！趕快去測來看您與產品的匹配度吧～"  # 沒有測試結果的情況

        # 根據測驗結果的關鍵字篩選 BestSkinType 欄位
        if latest_result and latest_result != "你還沒測驗膚質喔！趕快去測來看您與產品的匹配度吧～":
            if '乾性' in latest_result:
                query += " AND r.BestSkinType LIKE '%乾性%'"
            elif '油性' in latest_result:
                query += " AND r.BestSkinType LIKE '%油性%'"
            elif '混合' in latest_result:
                query += " AND r.BestSkinType LIKE '%混合%'"

        # 根據 SkinTypeRating 排序
        query += " ORDER BY r.SkinTypeRating DESC"

        # 執行查詢
        products = db.getSqlData(query, tuple(filters))
        
        # 返回匹配的產品
        return render_template('match.html', products=products, user_result=latest_result, username=username)
    except mysql.connector.Error as err:
        return f"Error: {str(err)}", 500
    finally:
        db.close()


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
    user_id = session.get('user_id')
    if not user_id:
        flash('請先登入。', 'warning')
        return redirect(url_for('login'))

    db = Database(**db_config)

    try:
        sql_user = "SELECT Username, Email, Password, CreatedAt FROM Users WHERE UserID = %s"
        data_user = (user_id,)
        user_results = db.getSqlData(sql_user, data_user)

        if user_results:
            user = user_results[0]
            username = user[0]
            email = user[1]
            password = user[2]
            created_at = user[3]

            sql_tests = "SELECT Sensitivity, Hydration, Oiliness, Result, TestDate FROM SkinTests WHERE Username = %s ORDER BY TestDate DESC"
            data_tests = (username,)
            skin_tests = db.getSqlData(sql_tests, data_tests)

            sql_reviews = """
            SELECT brand_name, product_name, size, price, category, rating, usage_info, experience_method, usage_season, usage_environment, review_content, SimplifiedReview, CreatedDate
            FROM Reviews
            WHERE Username = %s
            ORDER BY CreatedDate DESC
            """

            data_reviews = (username,)
            reviews = db.getSqlData(sql_reviews, data_reviews)

            sql_favorites = """
            SELECT f.product_name, f.brand, f.category, f.sizeprice, f.created_at, p.ImageURL
            FROM Favorites AS f
            JOIN Products AS p ON f.product_name = p.Name
            WHERE f.Username = %s
            """
            data_favorites = (username,)
            favorites = db.getSqlData(sql_favorites, data_favorites)

            section = request.args.get('section', 'skin-tests')

            return render_template('profile.html', username=username, email=email, password=password, created_at=created_at, skin_tests=skin_tests, reviews=reviews, favorites=favorites, section=section)
        else:
            flash('找不到用戶資料。', 'danger')
            return redirect(url_for('home'))
    except mysql.connector.Error as err:
        flash(f"資料庫錯誤: {str(err)}", 'danger')
        return redirect(url_for('home'))
    finally:
        db.close()


@app.route('/add_favorite', methods=["POST"])
def add_favorite():
    try:
        username = session.get('username')  # 從 session 中獲取使用者名稱

        # 檢查是否登入
        if not username:
            return jsonify({'status': 'error', 'message': '請登入即可收藏'}), 401

        data = request.json
        product_name = data.get('product_name')
        brand = data.get('brand')
        category = data.get('category')
        sizeprice = data.get('sizeprice')
        img_url = data.get('img_url')

        if not all([product_name, brand, category, sizeprice, img_url]):
            return jsonify({'status': 'error', 'message': 'Missing data'}), 400

        db = Database(**db_config)

        # 檢查是否已經存在該產品
        check_sql = "SELECT COUNT(*) FROM Favorites WHERE product_name = %s AND username = %s"
        existing = db.getSqlData(check_sql, (product_name, username))
        if existing and existing[0][0] > 0:
            return jsonify({'status': 'error', 'message': '此商品已經收藏囉'}), 409

        sql = """
        INSERT INTO Favorites (username, product_name, brand, category, sizeprice, img_url)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (username, product_name, brand, category, sizeprice, img_url)
        db.executeSql(sql, values)
        return jsonify({'status': 'success'}), 200

    except mysql.connector.Error as err:
        print(f"Database error: {str(err)}")
        return jsonify({'status': 'error', 'message': str(err)}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500
    finally:
        db.close()



@app.route('/add_comment', methods=['POST'])
def add_comment():
    user_id = session.get('user_id')
    if not user_id:
        flash('請先登入。', 'warning')
        return redirect(url_for('login'))

    # 獲取表單數據
    brand_name = request.form['brand_name']
    product_name = request.form['product_name']
    size = request.form['size']
    price = request.form['price']
    category = request.form['category']
    rating = request.form['rating']
    usage_info = request.form['usage_info']
    experience_method = request.form['experience_method']
    usage_season = request.form['usage_season']
    usage_environment = request.form['usage_environment']
    review_content = request.form['review_content']

    db = Database(**db_config)

    try:
        sql_insert = """
        INSERT INTO Reviews (brand_name, product_id, product_name, size, price, category, rating, usage_info, effect, experience_method, usage_season, usage_environment, review_content, Username)
        VALUES (%s, NULL, %s, %s, %s, %s, %s, %s, NULL, %s, %s, %s, %s, %s)
        """
        data_insert = (brand_name, product_name, size, price, category, rating, usage_info, experience_method, usage_season, usage_environment, review_content, session.get('username'))
        
        db.executeSql(sql_insert, data_insert)
        flash('評論已成功提交！', 'success')
    except mysql.connector.Error as err:
        flash(f"資料庫錯誤: {str(err)}", 'danger')
    finally:
        db.close()

    return redirect(url_for('profile', section='add-comment'))


@app.route('/sun', methods=["GET"])
def sun():
    db = Database(**db_config)
    try:
        # 查詢粉餅產品
        sql = "SELECT * FROM Products WHERE category LIKE %s"
        data = ("%防曬%",)  
        results = db.getSqlData(sql, data)
        
        products = []
        for row in results:
            product = {
                'id': row[0],
                'brand': row[1],
                'name': row[2],
                'category': row[3],
                'sizeprice': row[4],
                'des': row[5],
                'img': row[6],
            }
            
            # 查詢 NewReviewSummary 表中的 avg_rating
            rating_sql = "SELECT avg_rating FROM NewReviewSummary WHERE product_name = %s"
            rating_data = (row[2],)  # row[2] 是 product_name
            rating_result = db.getSqlData(rating_sql, rating_data)
            product['avg_rating'] = rating_result[0][0] if rating_result else None

            products.append(product)
        
        return render_template('sun.html', products=products, username=session.get('username'))
    except mysql.connector.Error as err:
        return f"Error: {str(err)}", 500
    finally:
        db.close()

@app.route('/liquid', methods=["GET"])
def liquid():
    db = Database(**db_config)
    try:
        # 查詢粉餅產品
        sql = "SELECT * FROM Products WHERE category LIKE %s"
        data = ("%粉底液%",)  
        results = db.getSqlData(sql, data)
        
        products = []
        for row in results:
            product = {
                'id': row[0],
                'brand': row[1],
                'name': row[2],
                'category': row[3],
                'sizeprice': row[4],
                'des': row[5],
                'img': row[6],
            }
            
            # 查詢 NewReviewSummary 表中的 avg_rating
            rating_sql = "SELECT avg_rating FROM NewReviewSummary WHERE product_name = %s"
            rating_data = (row[2],)  # row[2] 是 product_name
            rating_result = db.getSqlData(rating_sql, rating_data)
            product['avg_rating'] = rating_result[0][0] if rating_result else None

            products.append(product)
        
        return render_template('liquid.html', products=products, username=session.get('username'))
    except mysql.connector.Error as err:
        return f"Error: {str(err)}", 500
    finally:
        db.close()


@app.route('/cookie', methods=["GET"])
def cookie():
    db = Database(**db_config)
    try:
        # 查詢粉餅產品
        sql = "SELECT * FROM Products WHERE category LIKE %s"
        data = ("%粉餅%",)  
        results = db.getSqlData(sql, data)
        
        products = []
        for row in results:
            product = {
                'id': row[0],
                'brand': row[1],
                'name': row[2],
                'category': row[3],
                'sizeprice': row[4],
                'des': row[5],
                'img': row[6],
            }
            
            # 查詢 NewReviewSummary 表中的 avg_rating
            rating_sql = "SELECT avg_rating FROM NewReviewSummary WHERE product_name = %s"
            rating_data = (row[2],)  # row[2] 是 product_name
            rating_result = db.getSqlData(rating_sql, rating_data)
            product['avg_rating'] = rating_result[0][0] if rating_result else None

            products.append(product)
        
        return render_template('cookie.html', products=products, username=session.get('username'))
    except mysql.connector.Error as err:
        return f"Error: {str(err)}", 500
    finally:
        db.close()


@app.route('/products', methods=['GET'])  # 搜尋欄
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


@app.route('/product_detail/<string:product_name>', methods=["GET"])
def product_detail(product_name):
    db = Database(**db_config)
    try:
        sql = "SELECT * FROM Products WHERE name = %s"
        data = (product_name,)
        result = db.getSqlData(sql, data)

        #review_sql = "SELECT review_content, Keywords FROM Reviews WHERE product_name = %s"
        
        review_sql = "SELECT SimplifiedReview, Keywords FROM Reviews WHERE product_name = %s"
        
        # 查詢平均評分
        rating_sql = "SELECT avg_rating FROM NewReviewSummary WHERE product_name = %s"
        rating_data = (product_name,)
        rating_result = db.getSqlData(rating_sql, rating_data)
        avg_rating = rating_result[0][0] if rating_result else None

        review_data = (product_name,)
        reviews_result = db.getSqlData(review_sql, review_data)

        reviews = [review[0] for review in reviews_result] # 這裡的 review[0] 現在對應的是 `SimplifiedReview`

        keywords = reviews_result[0][1] if reviews_result else None

        if result:
            product = {
                'id': result[0][0],
                'brand': result[0][1],
                'name': result[0][2],
                'category': result[0][3],
                'sizeprice': result[0][4],
                'des': result[0][5],
                'img': result[0][6],
                'rating': avg_rating  # 使用 avg_rating 作為產品的評分

            }
            return render_template('des.html', product=product, reviews=reviews, keywords=keywords, username=session.get('username'))
        else:
            flash('找不到產品資料。', 'danger')
            return redirect(url_for('home'))
    except mysql.connector.Error as err:
        flash(f"資料庫錯誤: {str(err)}", 'danger')
        return redirect(url_for('home'))
    finally:
        db.close()


@app.route('/test', methods=["GET"])
def test():
    # 設定要查詢的使用者名稱
    target_username = 'miro'
    
    # 建立資料庫連線
    db = Database(**db_config)
    try:
        # 查詢 Reviews 表中 username 為 'miro' 的資料，只選擇需要的欄位
        sql = """
        SELECT username, CreatedDate, SimplifiedReview 
        FROM Reviews 
        WHERE username = %s 
        ORDER BY CreatedDate DESC 
        LIMIT 20
        """
        # 執行查詢並提供使用者名稱作為參數
        reviews_data = db.getSqlData(sql, (target_username,))
        
        # 將結果轉換成字典形式，以便前端渲染
        reviews_list = [
            {'username': review[0], 'created_date': review[1], 'simplified_review': review[2]} 
            for review in reviews_data
        ]
        
        return render_template('test.html', reviews=reviews_list)
    finally:
        db.close()



#@app.route('/simplify-review', methods=['POST'])
#login_required
#def simplify_review_route():
    if request.method == 'POST':
        try:
            db = Database(
                host=db_config['host'],
                port=db_config['port'],
                dbname=db_config['dbname'],
                username=db_config['username'],
                pwd=db_config['pwd']
            )

            # 查詢簡化評論
            results = db.getSqlData("SELECT review_content FROM Reviews WHERE SimplifiedReview IS NULL")
            simplified_reviews = []  # 儲存所有簡化的評論

            for row in results:
                review_content = row[0]
                simplified_review = simplify_review(review_content)  # 執行簡化邏輯
                simplified_reviews.append(simplified_review)  # 將簡化評論添加到列表
                db.executeSql("UPDATE Reviews SET SimplifiedReview = %s WHERE review_content = %s", 
                              (simplified_review, review_content))

            # 假設只返回最後一個簡化的評論
            latest_simplified_review = simplified_reviews[-1] if simplified_reviews else None

            return jsonify({'message': '評論已成功簡化！', 'simplified_review': latest_simplified_review})
        except Exception as e:
            return jsonify({'message': f'錯誤發生: {e}'}), 500

@app.route('/simplify-review', methods=['POST'])
@login_required
def simplify_review_route():
    data = request.get_json()  # 獲取請求中的 JSON 數據
    review_content = data.get('review_content')  # 獲取評論內容

    if review_content:
        try:
            # 創建 Database 實例
            db = Database(
                host=db_config['host'],
                port=db_config['port'],
                dbname=db_config['dbname'],
                username=db_config['username'],
                pwd=db_config['pwd']
            )

            # 直接調用 utils.py 中的簡化邏輯
            simplified_review, invalid_reason = simplify_review(review_content)

            # 儲存簡化評論或無效原因到資料庫
            if invalid_reason:
                # 儲存無效原因
                db.executeSql("UPDATE Reviews SET SimplifiedReview = %s WHERE review_content = %s", 
                              (invalid_reason, review_content))
                return jsonify({'message': '評論含有偏激字眼或太短，無法簡化。', 'simplified_review': None}), 400
            else:
                # 儲存簡化評論
                db.executeSql("UPDATE Reviews SET SimplifiedReview = %s WHERE review_content = %s", 
                              (simplified_review, review_content))
                return jsonify({'message': '評論已成功簡化！', 'simplified_review': simplified_review})

        except Exception as e:
            return jsonify({'message': f'錯誤發生: {e}'}), 500
        finally:
            db.close()  # 確保關閉資料庫連接
    else:
        return jsonify({'message': '未提供評論內容。'}), 400



if __name__ == "__main__":
    app.run(debug=True)  # 啟用偵錯模式