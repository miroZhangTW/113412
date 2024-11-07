document.getElementById('loginForm').addEventListener('submit', function(event) {
    event.preventDefault(); // 防止表單提交

    const email = document.getElementById('email').value; // 更改為 'email'
    const password = document.getElementById('password').value; // 更改為 'password'

    // 實際的登入邏輯，例如使用 Fetch API 來提交資料到後端
    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('登入成功！');
            // 這裡可以重定向到首頁或其他頁面
            window.location.href = '/'; 
        } else {
            alert(data.message || '登入失敗！');
        }
    })
    .catch(error => {
        console.error('登入錯誤:', error);
        alert('登入過程中發生錯誤！');
    });
});
