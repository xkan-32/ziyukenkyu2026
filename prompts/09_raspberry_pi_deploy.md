# Raspberry Pi 実機デプロイ — 観測基盤の起動（git 前提）

komatsuna-ai-agent の Raspberry Pi 観測基盤を **実機上で起動・検証** してください。

コード同期は **git のみ** を使います。rsync や手動コピーは行いません。

---

## 前提

- リポジトリ上の `edge/raspberry-pi/` 実装は完了済み（WSL 上でドライランテスト pass）
- 軽微な改善（ID マイクロ秒、パス正規化、boot JSON スキップ、systemd timer 修正）も反映済み
- **リモート git リポジトリ**（GitHub 等）が利用可能
- WSL 開発マシンで変更は **commit & push 済み**、またはデプロイ前に push する
- **Pi 上で SSH 接続済み**（`edge/raspberry-pi/ssh.sh` または Codex の SSH セッション）
- Pi に `git` がインストールされている
- Arduino UNO R4 WiFi が Pi に USB 接続されている（`/dev/ttyACM0` 想定）
- **本番散水はまだ解禁しない**（`ALLOW_WATER_COMMAND_FROM_PI=false` 維持）

---

## 目的

1. git で Pi 上に最新コードを配置する
2. Pi 上に Python 環境を構築する
3. 実 Arduino との `read` / `status` / `close` 通信を確認する
4. 観測 1 サイクルを実機で実行し、JSONL に記録されることを確認する
5. （可能なら）カメラ撮影を確認する
6. systemd timer で定期観測を有効化する

---

## 必ず最初に読むファイル

- `README.md`（次フェーズの範囲）
- `docs/04_detail_design.md`（通常観測シーケンス）
- `docs/07_safety.md`（水道接続前ゲート）
- `edge/raspberry-pi/.env.example`
- `edge/raspberry-pi/scripts/install.sh`
- `edge/raspberry-pi/systemd/komatsuna-agent.service`
- `edge/raspberry-pi/systemd/komatsuna-agent.timer`
- `edge/arduino/valve_controller/README.md`（シリアル JSON 契約）

---

## 安全制約（必須）

- `ALLOW_WATER_COMMAND_FROM_PI=false` を **必ず維持**
- `water` コマンドを Pi から送らない
- Arduino の `DRY_RUN_MODE` は **変更しない**（ユーザー確認なしで書き換えない）
- 水道接続・本番通水は行わない
- 12V 電源やバルブの配線を変更しない

---

## デプロイ先の想定（git clone 先）

| 項目 | 値 |
|------|-----|
| リポジトリ clone 先 | `~/komatsuna-ai-agent`（推奨） |
| アプリディレクトリ | `~/komatsuna-ai-agent/edge/raspberry-pi` |
| venv | `~/komatsuna-ai-agent/edge/raspberry-pi/.venv` |
| データ | `~/komatsuna-ai-agent/edge/raspberry-pi/data/local` |
| systemd WorkingDirectory | `~/komatsuna-ai-agent/edge/raspberry-pi` |

`/opt/` 配下に clone する場合は sudo と systemd パスの調整が必要です。本環境では **`~/komatsuna-ai-agent`（ユーザー `kansei`）** を使い、systemd unit は `/home/kansei/komatsuna-ai-agent/...` を前提としています（`edge/raspberry-pi/.ssh-env` の `RASPI_USER` 参照）。

---

## 作業手順

### Phase 0: WSL 開発マシン — push 確認

Pi に反映する前に、WSL 側で最新コードがリモートに載っていることを確認します。

```bash
cd /home/kansei/AI/ziyukenkyu2026

git status
git log -1 --oneline

# 未 push のコミットがあれば push（リモート名・ブランチは環境に合わせる）
git push origin main
# または: git push origin master
# または: git push origin HEAD
```

Pi 上で `git pull` したときに、WSL と同じコミットが取れる状態にしてから Phase 1 へ進んでください。

---

### Phase 1: Pi 上 — git clone / pull

**初回（clone 未実施）:**

```bash
cd ~
git clone <REMOTE_URL> komatsuna-ai-agent
cd ~/komatsuna-ai-agent
git branch --show-current
git log -1 --oneline
```

`<REMOTE_URL>` は実環境の GitHub / GitLab 等の URL に置き換えてください。  
SSH 鍵または HTTPS 認証が Pi 上で通ることを確認します。

**2 回目以降:**

```bash
cd ~/komatsuna-ai-agent
git fetch origin
git pull --ff-only
git log -1 --oneline
```

`git pull --ff-only` で fast-forward できない場合は、作業ツリーの変更やブランチずれを報告し、勝手に `git reset --hard` しないでください。

**clone / pull 後の確認:**

```bash
test -f edge/raspberry-pi/app/main.py
test -f edge/raspberry-pi/requirements.txt
test -f edge/raspberry-pi/.env.example
```

---

### Phase 2: Pi 上 — セットアップ

```bash
cd ~/komatsuna-ai-agent/edge/raspberry-pi

bash scripts/install.sh

# .env 作成（初回のみ。.env は git 管理外）
test -f .env || cp .env.example .env
```

`.env` の実機用設定（**必ず確認**）:

```env
ARDUINO_SERIAL_PORT=/dev/ttyACM0
ARDUINO_BAUD_RATE=115200
ALLOW_WATER_COMMAND_FROM_PI=false
DRY_RUN_MODE=false
CAMERA_ENABLED=true
EXPERIMENT_ROUND_ID=round_1
PLANTER_PROFILE_ID=ai_planter_a
LOCAL_DATA_DIR=./data/local
GCP_PROJECT_ID=
GCS_BUCKET_NAME=
LOG_LEVEL=INFO
```

- `DRY_RUN_MODE=false` … 実 Arduino 通信のため
- `ALLOW_WATER_COMMAND_FROM_PI=false` … **必ず維持**
- `.env` は **git に commit しない**

---

### Phase 3: Arduino 接続確認

```bash
ls -la /dev/ttyACM* /dev/ttyUSB* 2>/dev/null

groups
# Permission denied 時: sudo usermod -aG dialout $USER → 再ログイン

stty -F /dev/ttyACM0 115200 raw -echo min 0 time 20
exec 3<> /dev/ttyACM0
printf 'status\n' >&3
IFS= read -r -t 4 line <&3 && echo "$line"
exec 3>&-
exec 3<&-
```

期待: `{"status":"ok","command":"status",...}` が 1 行で返る。

boot JSON（`command":"boot"`）が混ざる場合もあります。Python クライアントは boot 行をスキップする実装済みです。

---

### Phase 4: 観測 1 サイクル（実機）

```bash
cd ~/komatsuna-ai-agent/edge/raspberry-pi
source .venv/bin/activate

python -m app.main once
```

確認:

```bash
tail -n 1 data/local/observations.jsonl | python -m json.tool
tail -n 1 data/local/soil_moisture_readings.jsonl | python -m json.tool
ls -la data/local/images/
grep ALLOW_WATER_COMMAND_FROM_PI .env
```

期待:

- `device_status`: `ok`（Arduino 通信成功時）
- `soil_moisture_raw` / `soil_moisture_percent` が null でない
- `image_local_path` が `images/...` の **相対パス**
- `id` にマイクロ秒が含まれる（例: `obs_20260704_120345_141777_ai_planter_a`）
- `local_queue.jsonl` に 1 行追加（GCP 未設定のため）

---

### Phase 5: カメラ確認（任意）

```bash
cd ~/komatsuna-ai-agent/edge/raspberry-pi
source .venv/bin/activate
bash scripts/test_camera.sh
```

- `libcamera-still` が使えれば実画像
- 使えなければ mock 画像にフォールバック（ログに warning）
- カメラ未接続なら `.env` で `CAMERA_ENABLED=false` でも可

---

### Phase 6: systemd 有効化

リポジトリ内の unit ファイルのパスが `~/komatsuna-ai-agent` と一致するか確認してから:

```bash
cd ~/komatsuna-ai-agent/edge/raspberry-pi

# 必要なら komatsuna-agent.service の WorkingDirectory / ExecStart / EnvironmentFile を
# 実際の clone 先に合わせて編集してから commit & push し、Pi で git pull する

sudo cp systemd/komatsuna-agent.service /etc/systemd/system/
sudo cp systemd/komatsuna-agent.timer /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable komatsuna-agent.timer
sudo systemctl start komatsuna-agent.timer

systemctl list-timers komatsuna-agent.timer
sudo systemctl start komatsuna-agent.service
journalctl -u komatsuna-agent.service -n 30 --no-pager
```

timer は `OnCalendar=hourly`（毎時 0 分）。

---

## 以降の更新フロー（git のみ）

コード変更後は毎回この順序です。

```bash
# WSL
cd /home/kansei/AI/ziyukenkyu2026
git add ...
git commit -m "..."
git push origin <branch>

# Pi
cd ~/komatsuna-ai-agent
git pull --ff-only
cd edge/raspberry-pi
source .venv/bin/activate
pip install -r requirements.txt   # requirements 変更時のみ
python -m app.main once           # 動作確認
sudo systemctl restart komatsuna-agent.timer  # systemd 変更時
```

---

## トラブルシューティング

| 症状 | 対処 |
|------|------|
| `git clone` 認証失敗 | Pi 上の SSH 鍵 / deploy key / PAT を確認 |
| `git pull --ff-only` 失敗 | `git status` でローカル変更を確認。`.env` や `data/local/` は git 管理外のはず |
| `Permission denied: /dev/ttyACM0` | `dialout` グループ追加、再ログイン |
| `No usable JSON response` | ポート番号確認、Arduino 再起動、USB ケーブル確認 |
| boot JSON のみ返る | 再送、Python クライアントは boot スキップ済み |
| カメラ失敗 | `CAMERA_ENABLED=false` で観測のみ継続 |
| systemd 失敗 | clone 先パス、`.venv`、`EnvironmentFile=.env` の存在を確認 |

---

## やってはいけないこと

- rsync や手動 scp でコードを同期する
- Pi 上で git 管理下ファイルを直接編集して pull と競合させる
- `git reset --hard` や force push（ユーザー明示指示なし）
- `ALLOW_WATER_COMMAND_FROM_PI=true` に変更
- `water` コマンド送信
- Arduino `config.h` の勝手な変更
- 水道接続・通水テスト
- `.env` や秘密情報を git commit する

---

## 受け入れ条件

- [ ] WSL から push 済み、Pi 上で `git pull` 後のコミットが一致
- [ ] Pi 上で `python -m app.main once` が exit 0
- [ ] 実 Arduino から `soil_moisture_raw` が取得できている
- [ ] `observations.jsonl` に実機観測が 1 行以上
- [ ] `ALLOW_WATER_COMMAND_FROM_PI=false` を確認
- [ ] systemd timer が enabled
- [ ] `water` コマンドを送っていない

---

## 完了報告フォーマット

1. 使用した git remote URL とブランチ名
2. Pi 上の clone 先パスと `git log -1 --oneline`
3. `/dev/ttyACM0` の有無と `status` 生 JSON 1 行
4. `python -m app.main once` のログ要約
5. `observations.jsonl` 最新 1 行
6. カメラ: 実撮影 / mock / スキップ のどれか
7. systemd timer の状態（`systemctl list-timers` 出力要約）
8. 問題があれば未解決事項

---

## 次フェーズ（このプロンプトの範囲外）

- GCP 最小構成（Terraform + Firestore/GCS）
- センサー実土壌校正（`tools/calibrate_soil_sensor.py`）
- AI 判断 API（`POST /judge`）
- 水道接続前安全ゲート完了後の `water` 解禁
