document.addEventListener('DOMContentLoaded', () => {
    const registerForm = document.getElementById('registerForm');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirmPassword');

    registerForm.addEventListener('submit', (e) => {
        // 验证密码强度
        const password = passwordInput.value;
        const confirmPassword = confirmPasswordInput.value;
        const passwordStrength = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$/;

        if (!passwordStrength.test(password)) {
            alert('密碼必須至少包含 8 個字符，包括字母和數字。');
            e.preventDefault(); // 阻止表单提交
            return;
        }

        // 确认密码匹配
        if (password !== confirmPassword) {
            alert('密碼與確認密碼不匹配。');
            e.preventDefault(); // 阻止表单提交
            return;
        }
    });
});
