# プロジェクト構成まとめ

## このアプリの言語・技術の全体像

```
ブラウザ（スマホ・PC）
  └── JavaScript (React)   ← 画面に見えるものはすべてこれ
        │
        │ API呼び出し（HTTP通信）
        ▼
サーバー（Render というクラウド）
  └── Python (FastAPI)     ← AI連携・データ処理はこれ
        │
        │ API呼び出し
        ▼
Anthropic API（Claude）    ← 英語紹介文を生成する AI
```

| 場所 | 言語 | 役割 |
|---|---|---|
| フロント（画面） | JavaScript（React + Vite） | 地図・ピン・ルート・カード・デモ再生の表示 |
| バックエンド（サーバー） | Python（FastAPI） | Anthropic API を呼んで紹介文を生成・返す |
| データ | JSON | 聖地の座標・名前・説明などを保存 |

---

## ルート直下

```
seichi-map/
├── frontend/          ← フロント（JavaScript）の全ファイル
├── backend/           ← バックエンド（Python）の全ファイル
├── seichi_data.json   ← 聖地データ（マスター）
├── CLAUDE.md          ← プロジェクト仕様書
├── STRUCTURE.md       ← このファイル
├── PROGRESS.md        ← 開発進捗メモ
├── SETUP.md           ← ローカル起動手順
└── .gitignore         ← GitHub に上げないファイルのリスト（.env など）
```

---

## frontend/（JavaScript・React）

**言語:** JavaScript  
**ビルドツール:** Vite（`npm run build` でブラウザ用ファイルに変換する）  
**デプロイ先:** Vercel（`https://seichi-map-rust.vercel.app`）

```
frontend/
├── src/
│   ├── App.jsx        ← ★ アプリの本体。ここがほぼ全て
│   ├── main.jsx       ← エントリーポイント（起動ファイル）
│   ├── index.css      ← 全体のスタイル（見た目）
│   └── App.css        ← App用スタイル（ほぼ未使用）
├── public/
│   └── seichi_data.json  ← 聖地データ（ブラウザから直接読む）
├── index.html         ← ベースとなるHTMLファイル
├── vite.config.js     ← Viteの設定
├── package.json       ← 使っているライブラリの一覧
├── .env               ← ローカル用のAPIキー（GitHub に上がらない）
└── .env.production    ← 本番用のAPIキー（Vercelビルド時に使用）
```

### App.jsx の中身

| 名前 | 何者か | 役割 |
|---|---|---|
| `haversine` | 関数 | 2点間の距離をメートルで計算する |
| `interpolatePath` | 関数 | ルート上のある時点（0〜1）の座標を返す |
| `Route` | コンポーネント（画面部品） | Google Maps でルートを線として描く |
| `Card` | コンポーネント | 聖地カードを表示。バックエンドを呼んでAI文章を取得する |
| `DemoControls` | コンポーネント | ▶️⏸⏮ ボタンとDEMO/LIVEトグルのUI |
| `App` | コンポーネント（親） | 全体の状態を管理。デモ再生・近接判定・カード表示を制御 |

### 変更しやすい定数（App.jsx の上部）

| 定数名 | 現在の値 | 意味 |
|---|---|---|
| `PROXIMITY_METERS` | `120` | 何メートル以内に近づいたらカードを出すか |
| `DEMO_DURATION_MS` | `30000` | デモ再生の長さ（ミリ秒）。30000 = 30秒 |

---

## backend/（Python・FastAPI）

**言語:** Python  
**フレームワーク:** FastAPI（Web API を簡単に作れるライブラリ）  
**デプロイ先:** Render（`https://seichi-map-backend.onrender.com`）

```
backend/
├── main.py            ← ★ サーバーの本体。APIエンドポイントを定義
├── requirements.txt   ← 使っているPythonライブラリの一覧
└── .env               ← Anthropic APIキー（GitHub に上がらない）
```

### APIエンドポイント（外から呼べる窓口）

| 呼び方 | URL | 何をするか |
|---|---|---|
| GET | `/health` | 「サーバー生きてる？」の確認。`{"status":"ok"}` を返す |
| POST | `/generate-intro` | 聖地情報を受け取り、Claude（AI）で英語紹介文を生成して返す |

---

## データ（seichi_data.json）

**言語:** JSON（データを記述するための書き方。プログラムではない）  
聖地1件につき1つのオブジェクトで、以下の情報を持つ：

| フィールド | 例 | 意味 |
|---|---|---|
| `spot_name_ja/en` | 宇治橋 / Uji Bridge | 聖地の名前 |
| `anime_title_ja/en` | 響け！ユーフォニアム | アニメのタイトル |
| `lat` / `lng` | 34.8915 / 135.8075 | 緯度・経度（地図上の位置） |
| `scene_description` | 主人公たちが渡る橋… | AIへの素材テキスト |
| `intro_short_en` | PLACEHOLDER… | AI生成前のデフォルト文 |

---

## デプロイ先まとめ

| 場所 | サービス | URL |
|---|---|---|
| フロント | Vercel | `https://seichi-map-rust.vercel.app` |
| バックエンド | Render | `https://seichi-map-backend.onrender.com` |

> **注意:** Render の無料プランは15分放置するとスリープする。  
> デモ前に `https://seichi-map-backend.onrender.com/health` を開いて起こすこと。
