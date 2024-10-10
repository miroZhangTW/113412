import mysql.connector

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


# --- 膚質匹配邏輯與更新程式 ---

# 定義中文膚質與相關關鍵詞
skin_type_keywords = {
    '乾性': ['保濕', '滋潤', '修護', '舒緩'],
    '油性': ['控油', '清爽', '痘', '輕薄'],
    '混合性': ['平衡', '輕薄', '敏感', '清爽']
}

def calculate_skin_type_score(text, skin_type):
    """根據關鍵詞計算膚質匹配度"""
    score = 0
    for keyword in skin_type_keywords[skin_type]:
        if keyword in text:
            score += 1
    return score * 100 / len(skin_type_keywords[skin_type]) if len(skin_type_keywords[skin_type]) > 0 else 0

if __name__ == "__main__":
    # 初始化連接資料庫
    db = Database(host="140.131.114.242", port=3306, dbname="113-113412", username="Beauty", pwd="6Eauty@110460")

    # 測試連接
    if db.test():
        print("成功連接到資料庫")
    else:
        print("無法連接到資料庫")

    # 從資料庫中抓取需要的資料
    try:
        # 加入 product_name, usage_info, effect, review_content 進行匹配
        results = db.getSqlData("SELECT product_id, product_name, usage_info, effect, review_content FROM Review")
        
        # 逐筆處理
        for row in results:
            product_id, product_name, usage_info, effect, review_content = row
            
            # 將所有欄位的內容合併
            combined_text = f"{product_name} {usage_info} {effect} {review_content}"
            
            # 計算膚質匹配度
            skin_type_scores = {skin_type: calculate_skin_type_score(combined_text, skin_type) for skin_type in skin_type_keywords}
            
            # 找出最佳膚質和匹配度
            best_skin_type = max(skin_type_scores, key=skin_type_scores.get)
            best_score = skin_type_scores[best_skin_type]
            
            # 顯示處理進度
            print(f"Processing Product: {product_name}, Best Skin Type: {best_skin_type}, Score: {best_score}")
            
            # 更新資料庫中的 SkinTypeRating 和 BestSkinType
            update_query = """
                UPDATE Review 
                SET SkinTypeRating = %s, BestSkinType = %s 
                WHERE product_id = %s
            """
            db.runSql(update_query, (best_score, best_skin_type, product_id))
        
        print("所有資料已處理完成")

    except mysql.connector.Error as err:
        print(f"處理資料時發生錯誤: {err}")

    # 最後關閉連接
    db.close()
