# 変更履歴

## 2026-04-27: NG一括貼り付け登録機能

### 概要
スタッフから送られてくる「日勤NG / 夜勤NG」のテキスト（LINE, メール等）をそのまま貼り付けて一括登録できる機能を追加。

### 対応した入力揺れ
- 区切り：カンマ `,` ・読点 `、` ・スペース ・全角スペース ・ドット `.`
- 月省略：`5/10,17`（同一行内で月を継承）
- 全角数字・旧字体・「日」付き：`５／１０日` `5.10日`
- 名前と日付が別行・同行の混在

### フロントエンド
- `src/lib/NgPasteBulk.svelte` — 日勤NG / 夜勤NG の貼り付けパネル（2つ配置）
- `src/lib/fuzzyMatch.js` — あいまいマッチング（部分一致＋レーベンシュタイン距離）
- `src/lib/StaffManager.svelte` — 一括パネルを統合。既存の「対応可否トグル」は維持

### バックエンド
- `backend/app/core/ng_parser.py` — テキストパーサー
- `backend/app/api/ng_entries.py` — `/ng_entries/bulk_parse`・`/ng_entries/bulk` エンドポイント追加

### テスト
- `backend/tests/test_ng_parser.py` — パーサーの10ケース
- `backend/tests/test_ng_bulk_api.py` — APIの3ケース
- 全50テスト通過

### 未解決→手動選択
プレビュー時にスタッフ一覧と名前が一致しない場合、プルダウンで正しい名前を選択してから登録可能。

## 2026-04-27: スタッフ追加・削除機能

### 概要
スタッフ / NGエントリ管理ページで、スタッフの追加・削除ができるようにした。

### フロントエンド
- `src/lib/StaffManager.svelte` — スタッフ一覧テーブルに「追加」「削除」UIを追加
  - 追加フォーム：氏名 + 日勤１番/日勤２番/夜勤 のチェックボックス
  - 各行に削除ボタン（確認ダイアログ付き）
- `src/lib/api.js` — `createMember`・`deleteMember` メソッド追加

### バックエンド
- `backend/app/api/members.py` — `POST /members`・`DELETE /members/{name}` エンドポイント追加
  - 追加時に同名スタッフが存在する場合は 409 Conflict を返す
  - 削除時に存在しない場合は 404 を返す

### テスト
- `backend/tests/test_members_api.py` — 追加・重複追加・削除・存在しない削除 の4ケースを追加
- テスト毎に settings.yaml を自動バックアップ・復元する fixture を導入
- 全57テスト通過
