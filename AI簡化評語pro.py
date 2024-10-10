import mysql.connector
import re

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

# 評語簡化 (提取產品信息)
def simplify_review(text, keywords):
    try:
        # 清理不必要的部分
        lines = [line for line in text.splitlines() if "大家好" not in line and "謝謝" not in line]
        cleaned_text = ' '.join(lines).strip()

        # 刪除逗號前面的單一字元
        cleaned_text = re.sub(r'(?<=\W)\w，', '', cleaned_text)

        # 刪除連續的多個感嘆號、問號、波浪號
        cleaned_text = re.sub(r'[!?~]{2,}', '', cleaned_text)

        # 刪除開頭的單一字元
        cleaned_text = re.sub(r'^\W*\w', '', cleaned_text)

        # 確保輸入文本的長度
        if len(cleaned_text) < 20:
            return keywords if keywords else text  # 如果文本過短，使用關鍵詞或原始文本

        # 提取關鍵產品信息
        product_info = []

        # 使用正則表達式匹配產品名稱
        product_name_match = re.search(r'(?<=的)[^，。]+', cleaned_text)
        if product_name_match:
            product_info.append(product_name_match.group(0).strip())
        
        # 匹配描述中的使用效果
        effectiveness_match = re.search(r'效果.*?[\。！]', cleaned_text)
        if effectiveness_match:
            product_info.append(effectiveness_match.group(0).strip())

        # 匹配使用經驗
        experience_match = re.search(r'使用.*?。', cleaned_text)
        if experience_match:
            product_info.append(experience_match.group(0).strip())

        # 構建返回的產品信息字符串，只返回提取出的內容
        summary = '，'.join(product_info)

        # 如果簡化結果過短，則使用 Keywords；如果 Keywords 不存在，則回退到原始文本
        return summary if len(summary) > 10 else (keywords if keywords else text)

    except Exception as e:
        print(f"Error during simplification: {e}")
        # 如果出現異常，使用 Keywords；如果 Keywords 不存在，則回退到原始文本
        return keywords if keywords else text

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
        results = db.getSqlData("SELECT review_content, Keywords FROM Review")
        for row in results:
            review_content = row[0]
            keywords = row[1]  # 獲取關鍵詞
            print(f"Original review content: {review_content}")  # 打印原始评语
            simplified_review = simplify_review(review_content, keywords)
            print(f"Simplified review: {simplified_review}\n")
            
            # 儲存簡化評論到資料庫
            db.runSql("UPDATE Review SET SimplifiedReview = %s WHERE review_content = %s", (simplified_review, review_content))
    except mysql.connector.Error as err:
        print(f"查詢數據時發生錯誤: {err}")

    # 最後關閉連接
    db.close()
