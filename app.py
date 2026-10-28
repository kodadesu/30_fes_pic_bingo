import os
from flask import Flask, render_template, request, redirect, url_for
import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv
import requests
from flask import request, abort

# .envファイルから環境変数を読み込む
load_dotenv()

# Cloudinaryの設定
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

app = Flask(__name__)

def get_bingo_items():
    """Cloudinaryの '30_fes' フォルダから保存済みの画像を自動取得してビンゴの状態を復元する"""
    items = {i: {"id": i, "title": f"お題 {i}", "image_url": None} for i in range(1, 31)}
    
    try:
        # '30_fes' フォルダ内のリソース（画像）を最大50件取得
        result = cloudinary.api.resources(
            type="upload",
            prefix="30_fes/",
            max_results=50
        )
        
        for resource in result.get("resources", []):
            public_id = resource.get("public_id") # 例: "30_fes/item_5"
            secure_url = resource.get("secure_url")
            
            # public_id から "item_X" の番号を抽出して紐付ける
            for i in range(1, 31):
                if public_id == f"30_fes/item_{i}":
                    items[i]["image_url"] = secure_url
                    break
    except Exception as e:
        print(f"Cloudinaryからのデータ読み込みエラー: {e}")
        
    return items

@app.route('/')
def index():
    bingo_items = get_bingo_items()
    completed_count = sum(1 for item in bingo_items.values() if item["image_url"] is not None)
    return render_template('index.html', items=bingo_items.values(), completed_count=completed_count)

@app.route('/delete/<int:item_id>', methods=['POST'])
def delete_image(item_id):
    try:
        # 正しいパス指定でCloudinaryから画像を削除
        cloudinary.uploader.destroy(f"30_fes/item_{item_id}")
    except Exception as e:
        print(f"削除エラー: {e}")
    return redirect(url_for('index'))


# LINEにプッシュ通知を送る関数
def send_line_notification(item_id):
    access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.getenv("LINE_USER_ID")
    
    if not access_token or not user_id:
        return # 設定されていない場合は何もしない

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    data = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": f"📸 30 Fes BINGO\nお題 {item_id} の写真がアップロードされました！"
            }
        ]
    }
    
    try:
        requests.post(url, headers=headers, json=data)
    except Exception as e:
        print(f"LINE通知エラー: {e}")


# 友だち追加やメッセージ送信があったときにLINEから自動で呼び出される窓口（Webhook）
@app.route('/callback', methods=['POST'])
def callback():
    body = request.get_json(silent=True)
    if not body:
        return 'OK'
    
    events = body.get('events', [])
    for event in events:
        # メッセージが送信されてきた場合
        if event.get('type') == 'message':
            user_id = event.get('source', {}).get('userId')
            print("========================================")
            print(f"★ 取得したお友達のユーザーID: {user_id}")
            print("========================================")
            
    return 'OK'

# アップロード処理 ＆ LINE通知
@app.route('/upload/<int:item_id>', methods=['POST'])
def upload(item_id):
    if 'image' not in request.files:
        return redirect(url_for('index'))
    
    file = request.files['image']
    if file.filename == '':
        return redirect(url_for('index'))
    
    if file:
        try:
            cloudinary.uploader.upload(
                file,
                folder="30_fes",
                public_id=f"item_{item_id}",
                overwrite=True
            )
            
            # ★ アップロード成功後にLINE通知を送る！
            send_line_notification(item_id)
            
        except Exception as e:
            print(f"アップロードエラー: {e}")
            
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)