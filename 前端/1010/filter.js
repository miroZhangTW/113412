       /*篩選*/
       function showPopup() {
            document.getElementById('overlay').style.display = 'flex';
        }

        function selectOption(button) {
            var selectedValue = button.value;
            var buttons = button.parentNode.querySelectorAll('button');
            buttons.forEach(function(btn) {
                btn.style.backgroundColor = btn.value === selectedValue ? '#ff6f61' : '#ffcccb';
            });
        }

        function search() {
            const query = document.getElementById('searchInput').value;
            // 执行搜索操作，例如显示搜索结果或者其他操作
            alert('您搜尋了: ' + query);
        }

        function calculateSkinType() {
            var selectedButtons = document.querySelectorAll('button[style="background-color: rgb(255, 111, 97);"]');
            var totalScore = 0;
            selectedButtons.forEach(function(btn) {
                totalScore += parseInt(btn.value);
            });
            var averageScore = totalScore / 3;

            var resultText;
            if (averageScore <= 2) {
                resultText = "非常敏感且非常乾燥或非常油膩";
            } else if (averageScore <= 3) {
                resultText = "敏感且乾燥或油膩";
            } else if (averageScore <= 4) {
                resultText = "敏感且稍微乾燥或稍微油膩";
            } else {
                resultText = "較不敏感且正常水分與油脂";
            }

            var email = prompt("請輸入您的email:");
            var output = "您的膚質檢測結果：" + resultText + "<br><br>根據您的膚質檢測，適合的產品有：<br>";
            // 在這裡添加適合的產品
            // output += "產品1<br>";
            // output += "產品2<br>";
            // output += "產品3<br>";
            document.getElementById("result").innerHTML = output;
        }

        function hidePopup() {
            document.getElementById('overlay').style.display = 'none';
        }
