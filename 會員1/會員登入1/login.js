document.getElementById('loginForm').addEventListener('submit', function(event) {
    event.preventDefault(); // 防止表單提交

    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    // 模擬登入過程
    console.log('電子郵件:', email);
    console.log('密碼:', password);

    // 登入成功提示
    alert('登入成功！');
});
