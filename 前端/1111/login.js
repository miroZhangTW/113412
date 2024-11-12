document.getElementById('loginForm').addEventListener('submit', function(event) {
    event.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

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
