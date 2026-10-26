# CLAUDE.md

火安服裝審查教官:一個跑在本機的 Discord bot,用 `claude -p` 審查火舞社社員練舞前的全身自拍是否符合火安服裝標準,並把結果記進 Excel。

## 開始任何工作前

先讀 `docs/architecture.md`。行為規則、資料格式、防護設計都以它為準;需求原文在 `docs/requirements.md`。兩份文件與實作不一致時,先問使用者,不要自行決定。

## 四段防護

`docs/architecture.md` 第 12 節定義四段防護。程式裡每一段都要用清楚的註解標出開始與結束,之後教學會逐段開關來對照效果:

```python
# ===== 防護 N 開始:(名稱) =====
...
# ===== 防護 N 結束 =====
```

| 編號 | 名稱 | 位置 |
|---|---|---|
| 1 | claude -p 只能讀到當次那一張照片(暫時工作資料夾、只開讀檔工具) | `reviewer.py` |
| 2 | 上傳者打的字與照片裡的字只當資料,不交給 claude 當指令 | `reviewer.py` |
| 3 | 暱稱轉檔名前清掉 `/`、`\`、`..`、`:` 等路徑字元 | `sanitize.py` |
| 4 | 寫進 Excel 的文字以 `=`、`+`、`-`、`@` 開頭時轉成純文字 | `sanitize.py`(`storage.py` 寫入時呼叫) |

- **一開始四段全部開啟。** 關掉防護是之後在測試頻道做的對照實驗,不要自己先關。
- 每段防護彼此獨立,各自包在自己的標記區塊內,不要把兩段的程式混在一起。

## 不可 commit 的東西

- **`.env` 不可以 commit 進 git。** 裡面有 `DISCORD_TOKEN`。只能 commit `.env.example`(只放假範例)。
- **`DATA_DIR` 裡的照片和 Excel 不要 commit**(`photos/`、`work/`、`records.xlsx`、`pending.jsonl`、`bot.log`),裡面是社員的個人資料。
- commit 前用 `git status` 確認這些檔案沒有出現在待 commit 清單裡;如果出現,先停下來處理 `.gitignore`。
- 萬一 token 已經被 commit 過,通知使用者到 Discord 開發者後台重設 token。
