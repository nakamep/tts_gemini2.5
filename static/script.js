// グローバル変数
let audioPlayer = null;
let apiStatus = false;
let statusCheckInterval = null;

// DOMが読み込まれたら実行
document.addEventListener('DOMContentLoaded', function() {
    // 要素の取得
    const statusIcon = document.getElementById('status-icon');
    const statusText = document.getElementById('status-text');
    const textInput = document.getElementById('text-input');
    const playButton = document.getElementById('play-button');
    const logArea = document.getElementById('log-area');
    
    // 初期化
    initializeApp();
    
    // 再生ボタンのイベントリスナー
    playButton.addEventListener('click', function() {
        if (textInput.value.trim() === '') {
            addLog('テキストが入力されていません', 'error');
            return;
        }
        
        generateAndPlaySpeech(textInput.value);
    });
    
    // アプリケーションの初期化
    function initializeApp() {
        addLog('アプリケーションを初期化中...', 'info');
        checkApiStatus();
        
        // 定期的なAPI状態チェックを設定（30秒ごと）
        statusCheckInterval = setInterval(checkApiStatus, 30000);
    }
    
    // API状態の確認
    function checkApiStatus() {
        updateStatusUI('loading', 'API状態確認中...');
        
        fetch('/status')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'ok') {
                    apiStatus = true;
                    updateStatusUI('ok', 'API接続正常');
                    playButton.disabled = false;
                    addLog('Gemini TTS APIに接続しました', 'success');
                } else {
                    apiStatus = false;
                    updateStatusUI('error', data.message || 'API接続エラー');
                    playButton.disabled = true;
                    addLog(`API接続エラー: ${data.message}`, 'error');
                }
            })
            .catch(error => {
                apiStatus = false;
                updateStatusUI('error', 'サーバー接続エラー');
                playButton.disabled = true;
                addLog(`サーバー接続エラー: ${error.message}`, 'error');
            });
    }
    
    // 音声生成と再生
    function generateAndPlaySpeech(text) {
        // 既存の音声プレーヤーを停止
        if (audioPlayer) {
            audioPlayer.pause();
            audioPlayer = null;
        }
        
        addLog(`音声生成リクエスト: "${text.substring(0, 30)}${text.length > 30 ? '...' : ''}"`, 'info');
        updateStatusUI('loading', '音声生成中...');
        playButton.disabled = true;
        
        fetch('/tts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: text })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.message || '音声生成に失敗しました');
                });
            }
            return response.blob();
        })
        .then(blob => {
            const audioUrl = URL.createObjectURL(blob);
            audioPlayer = new Audio(audioUrl);
            
            audioPlayer.onended = function() {
                addLog('音声再生完了', 'success');
                updateStatusUI('ok', 'API接続正常');
                playButton.disabled = false;
            };
            
            audioPlayer.onerror = function() {
                addLog('音声再生エラー', 'error');
                updateStatusUI('error', '音声再生エラー');
                playButton.disabled = false;
            };
            
            addLog('音声生成完了、再生開始', 'success');
            audioPlayer.play();
        })
        .catch(error => {
            addLog(`音声生成エラー: ${error.message}`, 'error');
            updateStatusUI('error', error.message);
            playButton.disabled = false;
            checkApiStatus(); // API状態を再確認
        });
    }
    
    // ステータスUIの更新
    function updateStatusUI(status, message) {
        statusIcon.className = 'status-icon ' + status;
        statusText.textContent = message;
    }
    
    // ログの追加
    function addLog(message, type = 'info') {
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${type}`;
        
        const timestamp = new Date().toLocaleTimeString();
        logEntry.textContent = `[${timestamp}] ${message}`;
        
        logArea.appendChild(logEntry);
        logArea.scrollTop = logArea.scrollHeight; // 自動スクロール
    }
});
