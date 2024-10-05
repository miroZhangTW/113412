const express = require('express');
const bodyParser = require('body-parser');
const { exec } = require('child_process');

const app = express();
app.use(bodyParser.json()); // 解析 JSON 資料

// 定義一個 POST 路由，處理表單提交
app.post('/submit', (req, res) => {
    const { field1, field2 } = req.body;  // 從前端接收資料

    // 調用 Python 程式
    const pythonProcess = exec(`python3 db.py ${field1} ${field2}`);

    pythonProcess.stdout.on('data', (data) => {
        console.log(data.toString());
        res.send('資料已成功提交到資料庫');
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(data.toString());
        res.status(500).send('資料提交失敗');
    });
});

// 啟動伺服器，並監聽在埠號 3000
app.listen(3000, () => {
    console.log('伺服器運行於 http://localhost:3000');
});
