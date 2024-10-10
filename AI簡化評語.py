import mysql.connector
from transformers import pipeline

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

    def runSql(self, sql, data=None):
        """執行 SQL 插入、更新、刪除等語句"""
        self.setServer()
        cursor = self.Server.cursor()
        try:
            if data is None:
                cursor.execute(sql)
            else:
                cursor.execute(sql, data)
            self.Server.commit()  # 提交更改
        finally:
            cursor.close()

    def getSqlData(self, sql):
        """執行查詢並返回結果集"""
        self.setServer()
        cursor = self.Server.cursor()
        try:
            cursor.execute(sql)
            return cursor.fetchall()  # 返回查詢結果
        finally:
            cursor.close()

    def close(self):
        """關閉資料庫連線"""
        if self.Server and self.Server.is_connected():
            self.Server.close()

# 创建总结生成器
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# 評語簡化 (摘要)
def simplify_review(text):
    try:
        # 确保输入文本不是空的并且长度合适
        if not text or len(text) > 1024:
            text = text[:1024]  # 截断至最大长度
        
        # 直接使用文本字符串作为输入
        summary = summarizer(text, max_length=30, min_length=5, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        print(f"Error during summarization: {e}")
        return text  # 返回原始文本以防止程序崩溃

# --- 使用示例 ---

if __name__ == "__main__":
    # 初始化連接資料庫
    db = Database(host="140.131.114.242", port=3306, dbname="113-113412", username="Beauty", pwd="6Eauty@110460")

    # 測試連接
    if db.test():
        print("成功連接到資料庫")
    else:
        print("無法連接到資料庫")

    # 查詢數據
    try:
        results = db.getSqlData("SELECT review_content FROM Review")
        for row in results:
            review_content = row[0]
            print(f"Original review content: {review_content}")  # 打印原始评语
            simplified_review = simplify_review(review_content)
            print(f"Simplified review: {simplified_review}")
    except mysql.connector.Error as err:
        print(f"查詢數據時發生錯誤: {err}")

    # 最後關閉連接
    db.close()
