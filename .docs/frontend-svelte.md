PROJECT CORE RULE（最小憲法）
1. 原則
技術は可変、設計思想は固定

依存は一方向

再現性を最優先

AIが迷わない構造にする


2. 全体構造
project-root/
├─ backend/
├─ frontend/
├─ docker/
├─ tests/
├─ .docs/
└─ README.md
勝手に構造を崩さない。

3. Frontend Rule（技術非依存）
レイヤー固定
Presentation → State → Application → Infrastructure
Shared（utils / types / constants）は全層参照可。
禁止
UIでAPI直呼び

レイヤー逆流

循環依存

1000行超の単一ファイル

SvelteKitを利用していても、FrontendはUI・画面遷移・表示状態に責務を限定する
FastAPIを採用している構成では、業務ロジック・API本体・認証中核・永続化処理をFrontend側へ持ち込まない
SvelteKitの server route や server load は、FastAPIと責務が重複しない場合にのみ使用する
既存でFastAPIに存在するAPI、入力検証、データ変換、認証処理をSvelte/SvelteKit側へ重複実装しない


4. Backend Rule（Python）
必須
Python管理は uv

pyproject.toml + uv.lock 使用

uv.lock は必ずコミット

禁止
pip単独使用

poetry併用

requirements.txt手動管理

直接 python 実行

実行例
uv venv
uv add fastapi
uv run python app/main.py
uv run pytest

FastAPIはバックエンドの正本として扱う
API仕様、業務ルール、入力検証、認証・認可、WebSocket処理の責務をBackendに集約する
Frontend都合で同等ロジックを別実装せず、必要なら共通化またはAPI化で解決する

5. Docker Rule
Docker内でも uv 使用

lockベースで依存同期

開発と本番の差異を最小化


6. テスト方針
Application層は必ずテスト

Infrastructureはモック可能設計

UIテストは任意


7. 強制分離
必ず外部化：
API通信

状態管理

ビジネスロジック

型・定数

共通関数

UI内に閉じ込めない。

FrontendとBackendで同じ責務を二重管理しない
SvelteKitとFastAPIが共存する場合、どちらを正本にするかを先に決めてから実装する
迷った場合は、UIはFrontend、APIと業務ロジックはFastAPIを優先する

8. AI実装規律
AIは：
レイヤー越境しない

APIをUIに直書きしない

uv前提で依存追加

テスト可能構造で実装

SvelteKitとFastAPIの両方に同種の処理を増やさない
既存責務の所在を確認してから追加実装する
二重化が避けられない場合は、理由と正本をコメントまたはドキュメントに明記する


