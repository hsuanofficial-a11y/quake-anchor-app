
# 地震速報主播稿生成器

這是一個可直接拿去做黑客松展示的 MVP：
上傳中央氣象署地震速報圖卡，系統會自動生成：

- 主播可直接朗讀的文稿
- 一行新聞標題

## 1) 功能特色

- 直接讀圖，不必先做 OCR
- 輸出格式固定，方便主播或編輯台直接使用
- 適合部署成網站，打開網址就能上傳圖卡
- 可以很容易再擴充成：
  - 自動語音播報
  - 地震資料庫歸檔
  - LINE Bot / Slack Bot
  - 多語系版本

## 2) 本機啟動

先安裝套件：

```bash
pip install -r requirements.txt
```

設定環境變數：

```bash
export OPENAI_API_KEY="你的_API_Key"
export OPENAI_MODEL="gpt-4.1-mini"
```

啟動：

```bash
python app.py
```

打開瀏覽器：
`http://localhost:8000`

## 3) 部署到 Render

### 建立環境變數
在 Render 後台新增：

- `OPENAI_API_KEY`
- `OPENAI_MODEL`（可選，預設 `gpt-4.1-mini`）

### Build Command
```bash
pip install -r requirements.txt
```

### Start Command
```bash
gunicorn app:app
```

部署完成後，Render 會給你一個固定網址。

## 4) 專案結構

```text
quake_anchor_app/
├─ app.py
├─ requirements.txt
├─ render.yaml
├─ Procfile
└─ templates/
   └─ index.html
```

## 5) 可進一步優化的方向

- 加入「範例文風」切換
- 增加「更口語 / 更正式」模式
- 自動比對 AI 讀出的數字與關鍵欄位
- 儲存歷史圖卡與生成結果
- 匯出成 Word、字幕條或跑馬燈格式
