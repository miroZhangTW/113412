import pandas as pd
from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
import pymysql


# 假設你有一個自定義的 Database 類來處理資料庫連接
class Database:
    def __init__(self, host, port, dbname, username, pwd):
        self.connection = self.connect_db(host, port, dbname, username, pwd)

    def connect_db(self, host, port, dbname, username, pwd):
        import pymysql
        return pymysql.connect(host=host, port=port, user=username, password=pwd, database=dbname)

    def getSqlData(self, sql):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                return result
        except Exception as e:
            print(f"SQL 查詢出錯: {e}")
            return None

    def runSql(self, sql, params):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, params)
                self.connection.commit()
        except Exception as e:
            print(f"執行 SQL 更新出錯: {e}")

    def close(self):
        self.connection.close()

class Database:
    def __init__(self, host, port, dbname, username, pwd):
        self.host = host
        self.port = port
        self.dbname = dbname
        self.username = username
        self.pwd = pwd
        self.connection = None

    def connect_db(self):
        self.connection = pymysql.connect(host=self.host, port=self.port,
                                           user=self.username, password=self.pwd, 
                                           database=self.dbname)

    def getSqlData(self, sql):
        if self.connection is None:
            self.connect_db()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql)
                return cursor.fetchall()
        except Exception as e:
            print(f"SQL 查詢出錯: {e}")
            return None
        finally:
            self.close()

    def runSql(self, sql, params):
        if self.connection is None:
            self.connect_db()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, params)
                self.connection.commit()
        except Exception as e:
            print(f"執行 SQL 更新出錯: {e}")
        finally:
            self.close()

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None


# 建立資料庫連接
db = Database(host="140.131.114.242", port=3306, dbname="113-113412", username="Beauty", pwd="6Eauty@110460")

# 獲取產品評語
def get_reviews_from_db():
    sql = "SELECT product_id, review_content FROM Review"
    return db.getSqlData(sql)

# 關鍵字提取函數
def extract_keywords(review, n_keywords=5):
    vectorizer = TfidfVectorizer(stop_words='english', max_features=n_keywords)
    X = vectorizer.fit_transform([review])
    keywords = vectorizer.get_feature_names_out()
    return ', '.join(keywords)

# 判斷最佳膚質
def determine_best_skin_type(keywords):
    skin_types = ['乾性', '油性', '混合性', '敏感性']
    for skin_type in skin_types:
        if skin_type in keywords:
            return skin_type
    return '不明'

# 情感分析並更新膚質評分
def sentiment_analysis_with_skin_type(review):
    sentiment_analyzer = pipeline('sentiment-analysis')
    # 將長文本分割為最多 512 個字符的段落
    chunks = [review[i:i + 512] for i in range(0, len(review), 512)]
    
    sentiment_scores = []
    for chunk in chunks:
        sentiment = sentiment_analyzer(chunk)[0]
        sentiment_scores.append(sentiment['label'])

    # 計算最終情感分數
    final_sentiment = 'POSITIVE' if sentiment_scores.count('POSITIVE') > sentiment_scores.count('NEGATIVE') else 'NEGATIVE'

    skin_types = ['乾性', '油性', '混合性', '敏感性']
    ratings = {skin_type: 0 for skin_type in skin_types}

    for skin_type in skin_types:
        if skin_type in review:
            ratings[skin_type] = 100 if final_sentiment == 'POSITIVE' else 0

    # 返回匹配度最高的膚質及其分數
    best_skin_type = max(ratings, key=ratings.get)
    best_score = ratings[best_skin_type]
    
    return best_score, best_skin_type

# 更新資料庫的函數
def update_best_skin_type_in_db(product_id, keywords, skin_type_rating, best_skin_type):
    sql = "UPDATE Review SET Keywords = %s, SkinTypeRating = %s, BestSkinType = %s WHERE product_id = %s"
    db.runSql(sql, (keywords, skin_type_rating, best_skin_type, product_id))

# 獲取資料
reviews_data = get_reviews_from_db()

# 逐筆處理並更新資料庫
for product_id, review_content in reviews_data:
    keywords = extract_keywords(review_content)  # 從每條評語提取關鍵字
    skin_type_rating, best_skin_type = sentiment_analysis_with_skin_type(review_content)
    update_best_skin_type_in_db(product_id, keywords, skin_type_rating, best_skin_type)

# 關閉資料庫連接
db.close()
