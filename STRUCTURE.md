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
│   ├── seichi_data.json     ← 聖地データ（ブラウザから直接読む）
│   ├── tourist_spots.json   ← 主要観光スポットデータ（通天閣・清水寺など10か所）
│   ├── icon-192.png         ← PWAアイコン（192×192）
│   ├── icon-512.png         ← PWAアイコン（512×512）
│   └── manifest.json        ← PWA設定ファイル（ホーム画面追加に必要）
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
| `TouristPopup` | コンポーネント | 観光スポットピンをクリックしたときに名前を表示するポップアップ |
| `DemoControls` | コンポーネント | ▶️⏸⏮ ボタン・速度切り替え・スクラバー（スライダー）のUI |
| `App` | コンポーネント（親） | 全体の状態を管理。デモ再生・近接判定・カード表示を制御 |

### 変更しやすい定数（App.jsx の上部）

| 定数名 | 現在の値 | 意味 |
|---|---|---|
| `PROXIMITY_METERS` | `3000` | 何メートル以内に近づいたらカードを出すか |
| `DEMO_SPEEDS` | `[10s, 30s, 60s]` | デモ再生の速度。画面上のボタンで切り替え可能 |

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
| POST | `/prefetch-intros` | 起動時に全聖地の紹介文をまとめて生成してキャッシュしておく |

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

---

## STRUCTURE.md 作成後の主な変更点

### AI紹介文まわり（A1〜A3）
- **キャッシュ:** サーバー側・ブラウザ側の両方でAI生成結果をキャッシュ（同じ聖地を2回API呼び出しせずに済む）
- **プリフェッチ:** アプリ起動時に全聖地の紹介文を `/prefetch-intros` でまとめて生成・保存
- **スピナー:** 紹介文を生成中はカードにローディングアニメーションを表示
- **フォールバック:** AI生成に失敗しても `intro_short_en` の元テキストを表示してクラッシュしない

### カードUI（A4〜A5、その後のtweak）
- スマホで地図が隠れないよう、カードは**デフォルト折りたたみ**に変更
- 「Read more」ボタンをタップすると本文が展開する（半透明ピル形状で強調）
- スマホ画面幅に合わせてカード・コントロールバーの幅が自動調整される

### 地図スタイル・ピン（B3〜）
- テーマカラーを紫（`#7c3aed`）に統一
- 聖地ピン: 紫の星型カスタムアイコン（`SPOT_ICON`）、scale 1.0
- 地図カラー: クリームトーン（黄色ベース）でアニメらしい明るい雰囲気に

### 観光スポット機能
- 主要観光スポット10か所をオレンジ丸ピンで地図に表示
- クリックで「日本語名（英語名）」のポップアップを表示
- データは `tourist_spots.json` に分離（コードを触らずデータ編集が可能）

### デモ機能強化
- **スクラバー:** スライダーでルート上の任意の位置に手動シーク可能（実験・確認用）
- **速度ボタン:** 画面上のボタンで 10秒 / 30秒 / 60秒 に切り替え可能
- **近接距離:** 3000m 以内に近づいたらカード表示（範囲内は維持、離れたら自動クローズ）
- **パルスアニメーション:** 近くの聖地ピンが拡縮して目立つように

### PWA対応（ホーム画面インストール）
- `manifest.json` 追加でスマホのホーム画面にアイコンとして追加できるようになった
- `index.html` に apple-touch-icon・theme-color のメタタグを追加
- アプリアイコン（192×192 / 512×512）を `public/` に配置
