import pandas as pd
from transformers import BertTokenizer, BertForSequenceClassification
from torch.utils.data import DataLoader, Dataset
import torch

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

# 建立資料庫連接
db = Database(host="140.131.114.242", port=3306, dbname="113-113412", username="Beauty", pwd="6Eauty@110460")

# 獲取產品評語
def get_reviews_from_db():
    sql = "SELECT product_id, review_content FROM Review"
    return db.getSqlData(sql)

# 獲取資料
reviews_data = get_reviews_from_db()

# 檢查數據是否正確加載
print("獲取的評價數據：", reviews_data)
if not reviews_data:
    raise ValueError("從資料庫未獲取到任何數據！")

# 將資料轉換為 DataFrame
df = pd.DataFrame(reviews_data, columns=["product_id", "review_content"])

# 檢查 DataFrame 的內容
print("DataFrame 內容：")
print(df.head())
print("數據總行數：", len(df))

# 確保 DataFrame 不是空的
if df.empty:
    raise ValueError("DataFrame 為空，請檢查資料庫查詢！")

# 分割評論和 ID
X = df['review_content']
ids = df['product_id']

# 檢查標籤範圍
print(f"最小標籤: {ids.min()}, 最大標籤: {ids.max()}")

# 如果標籤是從1開始，重新編碼標籤為從0開始 (這步驟根據實際數據需要來決定)
ids = ids - 1

# 檢查重新編碼後的標籤範圍
print(f"重新編碼後的最小標籤: {ids.min()}, 最大標籤: {ids.max()}")

# 使用 BERT 的 tokenizer
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

class ReviewDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len=512):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len
        print(f"Loaded {len(self.texts)} texts.")

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts.iloc[idx]
        label = self.labels.iloc[idx]

        encoding = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=self.max_len,
            return_token_type_ids=False,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt',
        )
        return {
            'text': text,
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'label': torch.tensor(label, dtype=torch.long)
        }

# 準備數據集
train_dataset = ReviewDataset(X, ids, tokenizer)
train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)

# 自動計算分類數目並設置 num_labels
num_labels = ids.nunique()
model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=num_labels)

# 設置設備 (使用 cuda 或 cpu)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)

# 定義優化器和損失函數
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-5)
loss_fn = torch.nn.CrossEntropyLoss()

# 訓練模型 (這裡簡單示範一個 epoch，實際情況應該更多)
for epoch in range(1):  # 調整為所需的 epoch 數
    model.train()
    for batch in train_loader:
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['label'].to(device)

        optimizer.zero_grad()

        outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
        loss = outputs.loss
        loss.backward()
        optimizer.step()

    print(f"Epoch {epoch + 1} completed. Loss: {loss.item()}")

# 預測和更新資料庫
model.eval()

def predict_and_update_reviews():
    predictions = []
    simplified_reviews = []
    for batch in train_loader:
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)

        with torch.no_grad():
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            preds = torch.argmax(outputs.logits, dim=1)
            predictions.extend(preds.cpu().numpy())
            simplified_reviews.extend(batch['text'])  # 根據實際需求生成簡化評論

    # 將預測結果寫入 df 並更新資料庫
    df['SkinTypeRating'] = predictions
    df['SimplifiedReview'] = simplified_reviews
    update_reviews_in_db(df)

# 更新資料庫中的評分和簡化評論
def update_reviews_in_db(df):
    for idx, row in df.iterrows():
        sql = "UPDATE Review SET SimplifiedReview = %s, SkinTypeRating = %s WHERE product_id = %s"
        db.runSql(sql, (row['SimplifiedReview'], row['SkinTypeRating'], row['product_id']))

# 預測並更新評論
predict_and_update_reviews()

# 關閉資料庫連接
db.close()
