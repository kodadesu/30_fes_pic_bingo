import os
from flask import Flask, render_template, request, redirect, url_for
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

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

# 30個のビンゴマス（お題）のデータ
bingo_items = {
    i: {"id": i, "title": f"お題 {i}", "image_url": None} for i in range(1, 31)
}

@app.route('/')
def index():
    completed_count = sum(1 for item in bingo_items.values() if item["image_url"] is not None)
    return render_template('index.html', items=bingo_items.values(), completed_count=completed_count)

@app.route('/upload/<int:item_id>', methods=['POST'])
def upload(item_id):
    if 'image' not in request.files:
        return redirect(url_for('index'))
    
    file = request.files['image']
    if file.filename == '':
        return redirect(url_for('index'))
    
    if file:
        try:
            # Cloudinaryへ画像をアップロード
            upload_result = cloudinary.uploader.upload(file)
            # Cloudinary上の安全な画像URLを取得
            image_url = upload_result.get("secure_url")
            
            # 該当マスの画像URLを更新
            bingo_items[item_id]["image_url"] = image_url
        except Exception as e:
            print(f"アップロードエラー: {e}")
            
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)