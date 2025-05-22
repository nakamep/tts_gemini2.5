import os
import json
import requests
from flask import Flask, request, jsonify, render_template, Response
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

app = Flask(__name__)

# Gemini API設定
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_TTS_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent"

def check_api_status():
    """Gemini APIの状態を確認する"""
    try:
        # APIキーが設定されているか確認
        if not GEMINI_API_KEY:
            return {"status": "error", "message": "APIキーが設定されていません"}
        
        # 簡単なテキストでAPIの応答を確認
        headers = {
            "Content-Type": "application/json"
        }
        
        params = {
            "key": GEMINI_API_KEY
        }
        
        # 正しいリクエスト形式でAPIをテスト
        data = {
            "contents": [{
                "parts": [{
                    "text": "こんにちは"
                }]
            }],
            "generation_config": {
                "response_modalities": ["AUDIO"],
                "speech_config": {
                    "voice_config": {
                        "prebuilt_voice_config": {
                            "voice_name": "ja-JP-Neural2-C"
                        }
                    }
                }
            }
        }
        
        response = requests.post(
            GEMINI_TTS_URL, 
            headers=headers,
            params=params,
            json=data
        )
        
        if response.status_code == 200:
            return {"status": "ok", "message": "API接続正常"}
        else:
            return {"status": "error", "message": f"APIエラー: {response.status_code} - {response.text}"}
    
    except Exception as e:
        return {"status": "error", "message": f"接続エラー: {str(e)}"}

@app.route('/')
def index():
    """メインページを表示"""
    return render_template('index.html')

@app.route('/status', methods=['GET'])
def status():
    """API状態を確認するエンドポイント"""
    result = check_api_status()
    return jsonify(result)

@app.route('/tts', methods=['POST'])
def text_to_speech():
    """テキストを音声に変換するエンドポイント"""
    try:
        # リクエストからテキストを取得
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({"status": "error", "message": "テキストが空です"}), 400
        
        # APIキーの確認
        if not GEMINI_API_KEY:
            return jsonify({"status": "error", "message": "APIキーが設定されていません"}), 500
        
        # Gemini TTS APIにリクエスト（修正版）
        headers = {
            "Content-Type": "application/json"
        }
        
        params = {
            "key": GEMINI_API_KEY
        }
        
        # 正しいリクエスト形式に修正
        payload = {
            "contents": [{
                "parts": [{
                    "text": text
                }]
            }],
            "generation_config": {
                "response_modalities": ["AUDIO"],
                "speech_config": {
                    "voice_config": {
                        "prebuilt_voice_config": {
                            "voice_name": "ja-JP-Neural2-C"  # 日本語音声
                        }
                    }
                }
            }
        }
        
        response = requests.post(
            GEMINI_TTS_URL, 
            headers=headers,
            params=params,
            json=payload
        )
        
        if response.status_code != 200:
            return jsonify({
                "status": "error", 
                "message": f"APIエラー: {response.status_code} - {response.text}"
            }), 500
        
        # レスポンスから音声データを取得
        response_data = response.json()
        
        # 修正: 正しいレスポンス構造からオーディオデータを取得
        audio_content = None
        try:
            # 新しいレスポンス構造
            audio_content = response_data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("inline_data", {}).get("data", "")
        except Exception:
            # 古い構造も試す
            audio_content = response_data.get("contents", [{}])[0].get("parts", [{}])[0].get("audio", {}).get("content", "")
        
        if not audio_content:
            return jsonify({
                "status": "error", 
                "message": "音声データが取得できませんでした"
            }), 500
        
        # 音声データを返す
        return Response(
            audio_content,
            mimetype="audio/mpeg"
        )
        
    except Exception as e:
        return jsonify({"status": "error", "message": f"エラー: {str(e)}"}), 500

if __name__ == '__main__':
    # 環境変数からポートを取得、なければデフォルト5000を使用
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
