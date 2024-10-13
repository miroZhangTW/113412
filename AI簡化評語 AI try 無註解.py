import mysql.connector
import re
from textblob import TextBlob
from transformers import pipeline, Trainer, TrainingArguments
from datasets import load_dataset
import pandas as pd

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
        if self.Server is None or not self.Server.is_connected():
            self.Server = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )

    def test(self):
        self.setServer()
        return self.Server.is_connected()

    def runSql(self, sql, data=None):
        self.setServer()
        cursor = self.Server.cursor()
        try:
            if data is None:
                cursor.execute(sql)
            else:
                cursor.execute(sql, data)
            self.Server.commit()
        finally:
            cursor.close()

    def getSqlData(self, sql):
        self.setServer()
        cursor = self.Server.cursor()
        try:
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    def close(self):
        if self.Server and self.Server.is_connected():
            self.Server.close()

def simplify_review(text):
    try:
        if len(text) < 50:
            return text
        
        lines = [line for line in text.splitlines() if "大家好" not in line and "謝謝" not in line]
        cleaned_text = ' '.join(lines).strip()
        cleaned_text = re.sub(r'\(.*?\)', '', cleaned_text)
        cleaned_text = re.sub(r'^[,，.。…、]+', '', cleaned_text)
        sentiment = TextBlob(cleaned_text)
        sentiment_score = sentiment.sentiment.polarity

        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        max_length_value = 50 if len(cleaned_text) >= 50 else 10
        max_token_length = 1024
        token_count = len(cleaned_text.split())

        if token_count > max_token_length:
            cleaned_text = ' '.join(cleaned_text.split()[:max_token_length])

        summary = summarizer(cleaned_text, max_length=max_length_value, min_length=1, do_sample=False)[0]['summary_text']

        if len(summary) < 10:
            return text

        summary = re.sub(r'^[!?~]+', '', summary)
        sentiment_text = "情感評分: {:.2f}".format(sentiment_score)
        summary += f" ({sentiment_text})"

        return summary

    except Exception as general_err:
        return f"處理失敗，原因: {general_err}"

def train_model(db):
    results = db.getSqlData("SELECT review_content, SimplifiedReview FROM Review WHERE SimplifiedReview IS NOT NULL")
    data = []
    for row in results:
        review_content = row[0]
        simplified_review = row[1]
        data.append({"text": review_content, "summary": simplified_review})

    df = pd.DataFrame(data)
    df.to_csv("dataset.csv", index=False)

    dataset = load_dataset("csv", data_files="dataset.csv")

    training_args = TrainingArguments(
        output_dir="./results",
        evaluation_strategy="epoch",
        learning_rate=5e-5,
        per_device_train_batch_size=16,
        num_train_epochs=3,
        weight_decay=0.01,
    )

    model = pipeline("summarization", model="facebook/bart-large-cnn")

    trainer = Trainer(
        model=model.model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["train"],
    )
    trainer.train()

if __name__ == "__main__":
    db = Database(host="140.131.114.242", port=3306, dbname="113-113412", username="Beauty", pwd="6Eauty@110460")
    if db.test():
        print("成功連接到數據庫")
    else:
        print("無法連接到數據庫")

    train_model(db)

    try:
        results = db.getSqlData("SELECT review_content FROM Review")
        for row in results:
            review_content = row[0]
            print(f"Original review content: {review_content}")
            simplified_review = simplify_review(review_content)
            print(f"Simplified review: {simplified_review}\n")
    except mysql.connector.Error as err:
        print(f"查詢數據時發生錯誤: {err}")

    db.close()
