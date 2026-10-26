# Discord Bot 設定步驟

這份文件帶你在 Discord Developer Portal 建立 bot、打開必要的開關、拿到 bot token、把 bot 邀進你自己的 Server。

**開始前請先完成** `docs/discord-server-setup.md`(你需要已經有自己的 Server 和 `CHANNEL_ID`)。

**名詞:**
- **Discord Developer Portal(開發者後台)**:Discord 給開發者管理機器人的網站。
- **Application(應用程式)**:你在開發者後台建立的「專案」,一個 application 裡面可以有一個 bot。
- **Bot**:會自己讀訊息、自己回話的帳號。你的 agent 就是用這個帳號登入 Discord。
- **Bot token**:bot 的密碼。拿到 token 的人就能完全控制這個 bot。

---

## ⚠️ 先看這一段:bot token 的規則

> **bot token 絕對不能:**
> - ❌ **貼給任何人**(同學、朋友、客服、網路論壇都不行)
> - ❌ **貼進這個對話**(包含貼給 Claude;不要叫 Claude 打開 `.env` 讀給你看)
> - ❌ **commit 進 git**、推上 GitHub(即使事後刪掉,歷史紀錄還是找得到)
> - ❌ **截圖**(連線的畫面、錯誤訊息裡都可能含 token)
>
> **為什麼這麼嚴:** 任何人拿到 token,就能用你的 bot 登入、讀它能看到的所有訊息、用你的 bot 發任何內容。
>
> **token 只能放在一個地方:** 你電腦上專案資料夾裡的 `.env` 檔(這個檔已經設定成不會被 git 收進去)。
>
> **萬一外洩了:** 立刻回到本文件的第三部分,按 **Reset Token**,舊的 token 馬上失效。不要猶豫,重設不花錢也沒有後果。

---

## 第一部分:建立 Application 和 Bot

1. 打開瀏覽器(Chrome 或 Edge),到 `https://discord.com/developers/applications`。
2. 如果要你登入,用**跟你建立 Server 同一個** Discord 帳號登入。
3. 看畫面**右上角**,點藍色按鈕 **「新增應用程式 / New Application」**。
4. 跳出視窗:
   1. 在 **「名稱 / Name」** 輸入 `火安服裝審查教官`(這是 bot 在 Discord 裡顯示的名字,之後可以改)。
   2. 勾選下面的同意條款(Discord 的開發者服務條款)。
   3. 點 **「建立 / Create」**。
   4. 如果出現「我不是機器人」的驗證,照指示完成。
5. **你應該看到:** 進到這個 application 的設定頁,左側有一排選單:`General Information`、`Installation`、`OAuth2`、`Bot`⋯⋯
6. 在左側選單點 **「Bot」**。
   - 新建立的 application 會自動有一個 bot 帳號,不用另外「新增 bot」。
   - 如果看到「Add Bot」按鈕,點它並確認。

---

## 第二部分:打開 Message Content Intent(一定要做)

### 為什麼一定要

**Intent** 是 Discord 的「權限開關」:機器人要先申報「我需要收到哪一類資料」,Discord 才會送給它。

**Message Content Intent** 控制 bot 能不能看到「訊息的內容和附件」。這個開關**沒打開**的話,bot 收到的訊息裡,**附件(照片)是空的**,agent 就看不到任何人傳的照片,完全無法運作。

這是 Discord 的「特權開關」,預設是關的,必須你自己到後台打開。

### 怎麼做

1. 還在 **Bot** 頁面,往下捲,找到 **「Privileged Gateway Intents」** 這一區。
2. 這一區有三個開關:
   - `Presence Intent`:**保持關閉**(我們不需要知道誰在線上)
   - `Server Members Intent`:**保持關閉**(我們不需要成員名單)
   - **`Message Content Intent`:把它打開**(開關變成藍色/綠色)
3. 往下捲到頁面最下面,會跳出一個提示條 **「Save Changes」**(儲存變更),點它。
4. **你應該看到:** 提示「Successfully updated」之類的訊息,重新整理頁面後 `Message Content Intent` 仍然是打開的。

> 你的 bot 在不到 100 個 Server 的情況下,這個開關自己打開就好,不需要送審。

### 順便關掉「公開 bot」

1. 還在 **Bot** 頁面,往上找 **「Public Bot」** 開關。
2. 把它**關閉**。
   - 原因:打開的話,任何人都能用邀請連結把你的 bot 邀進他們的 Server。你只想自己用。
3. 同樣按 **Save Changes** 儲存。

---

## 第三部分:拿到 Bot Token

1. 還在 **Bot** 頁面,往上找到 **「Token」** 這一區。
2. 點 **「重設權杖 / Reset Token」**。
   - 新建立的 bot 有時是顯示 `Reset Token`,不是顯示現成的 token。這是正常的。
3. 跳出確認視窗,點 **「是,沒錯!/ Yes, do it!」**。
   - 可能會要你輸入 Discord 密碼,或 2FA 驗證碼,照做。
4. **你應該看到:** Token 區出現一長串亂碼(很長,約 70 個字元,中間有兩個點),旁邊有 **「複製 / Copy」** 按鈕。
5. 點 **「複製 / Copy」**。

> ⚠️ **這串 token 只會完整顯示這一次。** 關掉頁面或重新整理後,你就看不到了,只能再 Reset 一次拿新的。

6. **馬上**照下一段把它放進 `.env`。不要貼到記事本以外的任何地方,不要貼到聊天軟體。

### 把 token 放進 .env(Windows)

**重要:Windows 記事本很容易把檔名存成 `.env.txt`,那樣程式讀不到。請照下面的步驟做。**

1. 先讓檔案總管顯示副檔名(只要做一次):
   1. 打開**檔案總管**。
   2. 點上方選單 **「檢視 / View」** → **「顯示 / Show」** → 勾選 **「副檔名 / File name extensions」**。
2. 在檔案總管打開 `C:\Users\user\FD-photos` 這個資料夾。
3. 在空白處按滑鼠右鍵 → **「新增 / New」** → **「文字文件 / Text Document」**。
4. 把檔名整個改成 `.env`(前面有一個點,後面**沒有** `.txt`)。出現「變更副檔名可能導致檔案無法使用」的警告時,按 **「是 / Yes」**。
5. 對 `.env` 按滑鼠右鍵 → **「開啟檔案 / Open with」** → **記事本 / Notepad**。
6. 輸入下面內容(把 `貼上你的token` 換成你剛複製的 token,用 `Ctrl + V` 貼上;`CHANNEL_ID` 填你在上一份文件記下的數字):

```
DISCORD_TOKEN=貼上你的token
CHANNEL_ID=貼上你的頻道ID
CLAUDE_MODEL=
DATA_DIR=C:\Users\user\FD-photos-data
SEMESTER_START=2026-09-01
```

   - 等號兩邊**不要**加空格、不要加引號。
   - `CLAUDE_MODEL` 先留空,等寫程式時一起決定。
7. 按 `Ctrl + S` 存檔,關掉記事本。
8. 確認這個檔**不會被 git 收進去**:在這個專案資料夾開終端機,輸入 `git status`。**你應該看不到** `.env` 出現在清單裡。如果看到了,**停下來**,不要 commit,先告訴我。

---

## 第四部分:決定權限,把 Bot 邀進你的 Server

### 為什麼要特別選權限

**權限**是 bot 在 Server 裡能做的事。原則是「**只給需要的**」:就算 bot 被人搞壞或 token 外洩,它能造成的傷害也有限。**不要給 `Administrator`(管理員)。**

### 這個 bot 只需要三個權限

| 權限(中文 / English) | 為什麼需要 |
|---|---|
| 檢視頻道 / View Channels | 看得到 `# 火安審查` 這個頻道 |
| 傳送訊息 / Send Messages | 回覆「處理中」和審查結果 |
| 讀取訊息歷史 / Read Message History | 回覆時要能指向對方的那則訊息(「回覆」功能需要) |

不需要:管理訊息、管理頻道、提及所有人、上傳檔案、新增表情符號⋯⋯都不要勾。

### 產生邀請連結

1. 在開發者後台,左側選單點 **「OAuth2」**。
2. 往下捲,找到 **「OAuth2 URL Generator」**(網址產生器)。
3. **Scopes(範圍)** 這一區,只勾 **`bot`**。其他都不要勾。
4. 勾了 `bot` 之後,下面會出現新的一區 **「Bot Permissions」**。只勾這三項:
   - ✅ `View Channels`
   - ✅ `Send Messages`
   - ✅ `Read Message History`
5. 如果有 **「Integration Type」** 的選項,選 **「Guild Install」**(裝到 Server)。
6. 頁面最下面有 **「Generated URL」**(產生的網址),點旁邊的 **「複製 / Copy」**。
   - 這個網址**不是**機密,它只是邀請連結。

### 邀請 bot 進你的 Server

1. 打開一個新的瀏覽器分頁,貼上剛才複製的網址,按 Enter。
2. 如果沒登入,用你的 Discord 帳號登入。
3. 在 **「新增至伺服器 / Add to Server」** 下拉選單,選你剛建的 Server(例如「火舞社審查測試」)。
   - 只有你**擁有或管理**的 Server 才會出現在清單。
4. 點 **「繼續 / Continue」**。
5. 下一頁會列出剛才勾的三個權限,確認沒有多餘的,點 **「授權 / Authorize」**。
6. 完成「我不是機器人」驗證。
7. **你應該看到:** 「已授權 / Authorized」或「成功」。

### 確認 bot 進來了

1. 回到 Discord,打開你的 Server。
2. 看畫面**最右邊**的成員清單。
3. **你應該看到:** 一個叫 `火安服裝審查教官` 的成員,旁邊有一個 **`APP`**(或 `BOT`)標籤。
4. 現在它會顯示**離線 / Offline**(灰色),這是正常的,因為你的 agent 程式還沒啟動。程式啟動後它會變成線上。

---

## 疑難排解

**成員清單看不到 bot**
- 可能沒授權成功,回到「邀請 bot 進你的 Server」重做。

**bot 在私人頻道裡看不到、之後不會反應**(把頻道設成私人後才會遇到)
1. 對 `# 火安審查` 按右鍵 → **「編輯頻道 / Edit Channel」** → **「權限 / Permissions」**。
2. 在 **「進階權限 / Advanced Permissions」** 點 **`+`**,搜尋 `火安服裝審查教官` 並加入。
3. 確認它的 `檢視頻道`、`傳送訊息`、`讀取訊息歷史` 是打勾(綠色 ✓)。

**忘記 token / 看不到 token 了**
- 回 Bot 頁面按 **Reset Token** 拿新的,然後更新 `.env`。舊的會立刻失效。

**懷疑 token 外洩**(貼錯地方、截圖流出、不小心 commit)
1. **立刻**回 Bot 頁面按 **Reset Token**。
2. 更新 `.env` 為新的 token。
3. 如果是不小心 commit 過,告訴我,我們一起處理 git 歷史。

**程式之後啟動時出現 `PrivilegedIntentsRequired` 之類的錯誤**
- 代表 Message Content Intent 沒打開或沒儲存成功,回第二部分重做,記得按 **Save Changes**。

---

## 這份文件做完後,你會有

- [ ] 一個 Discord application 和 bot
- [ ] **Message Content Intent 已打開並儲存**
- [ ] Public Bot 已關閉
- [ ] 專案資料夾裡有 `.env`,填了 `DISCORD_TOKEN` 和 `CHANNEL_ID`
- [ ] `git status` 看不到 `.env`
- [ ] bot 已在你的 Server 裡(離線狀態)
- [ ] bot 只有三個權限:檢視頻道、傳送訊息、讀取訊息歷史

這些都完成後,Discord 這邊就設定好了。接下來才會進入寫程式。
