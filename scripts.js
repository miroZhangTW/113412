document.getElementById('registerLink').addEventListener('click', function() {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerFormContainer').style.display = 'block';
});

document.getElementById('loginLink').addEventListener('click', function() {
    document.getElementById('registerFormContainer').style.display = 'none';
    document.getElementById('loginForm').style.display = 'block';
});

// 此處可以加入表單提交時的前端驗證和與後端的交互