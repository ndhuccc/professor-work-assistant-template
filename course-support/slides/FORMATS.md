# 投影片格式說明(老師用)

本資料夾存放各週的投影片。每週可以放一種或多種格式,學生在課程網站的 `slides/` 頁面下載。
網站上的下載頁由建置腳本自動產生,不需要手動維護。下載頁依週次分成頁籤(一週一個頁籤、一個表格),週次再多也不會擠成一張大表。

## 命名

- `lecNN.jbd.json`:JianBauDau 投影片(NN 為兩位數週次)
- `lecNN.pptx`:PowerPoint
- `lecNN.pdf`:PDF(適合列印)
- `lecNN.html`:單檔網頁(可離線開啟)

檔名與 `lectures/lecNN.md` 對應。同一週可以同時放多種格式。不符合這個命名的檔案會列在下載頁的「其他檔案」。

**同一週有多份教材時**,加一段代號:`lecNN-<代號>.<格式>`,例如 `lec02-parameter-estimation.jbd.json`、`lec02-bayes-networks.pdf`。代號用小寫英文與連字號,和該份講義的檔名一致(`lectures/lec02-parameter-estimation.md` 對應 `slides/lec02-parameter-estimation.jbd.json`)。網站的下載頁會把「沒有代號的」標為該週正課、有代號的標出代號,讓學生分得出必讀與自主學習。

## 格式與用途

| 格式 | 學生如何開啟 | 老師如何產生 | 注意事項 |
|---|---|---|---|
| JianBauDau JSON | JianBauDau 播放器(Windows):按 Ctrl+O 開啟 `.json`,或把檔案拖進視窗;也可用 JianBauDau 編輯器的 Open | JianBauDau 編輯器工具列的 **Export** | 圖片與影片會內嵌在檔案中,檔案可能很大;可能含講者備註 |
| PPTX | PowerPoint 或相容軟體 | 任何簡報軟體 | 沒有額外檢查 |
| PDF | 任何 PDF 閱讀器 | 任何方式匯出 | 無法互動 |
| HTML | 瀏覽器(離線即可開啟) | 單一檔案,不要引用外部資源 | 外部資源在離線時會失效 |

## 播放器下載

學生用的 JianBauDau 播放器(Windows 執行檔)連結會自動出現在網站的投影片下載頁:
<https://github.com/ndhuccc/IDL115/releases/download/player-v1.0.1/JianBauDau-Player-1.0.1.exe>

換新版時,修改 `scripts/build_docs.py` 的 `PLAYER_URL`。

## 老師的流程

1. 在 JianBauDau 編輯器完成簡報,按 **Export**,得到 `.json` 檔。
2. 把檔案放進 `slides/`,命名為 `lecNN.jbd.json`。
3. 執行檢查:

   ```bash
   python scripts/check_slides.py
   ```

   - **FAIL**:播放器無法正確播放,必須修正(例如匯入用的 page spec、孤兒節點、`asset:` 伺服器參照、`scene-point` 缺少 `referenceViewport`、使用 `enter-frame`、含 Frame 的場景不是「每個 Frame 恰好一個 step」;結構規則見 `.agents/skills/view-from-text/SKILL.md` §4B)。
   - **WARN**:可以播放,但請逐項確認(講者備註、電子郵件、疑似學號、檔案大小)。
4. 提交並推送。網站的 `slides/` 頁面會自動列出新檔案。

PPTX、PDF、HTML 直接放進來即可。`check_slides.py` 只檢查 `.jbd.json`。

## 發佈前必須確認

- **網站是公開的**:課程網站可以不登入直接開啟,因此 `slides/` 內的檔案也會公開。即使 Repo 是 Private,也是如此。
- **不要放進投影片**:講者備註中的個人資訊、成績、學號、解答(`labs/*/solution/` 的內容)、尚未考過的考題。
- **檔案大小**:超過 20 MB 會警告;超過 90 MB 會失敗(GitHub 單一檔案上限為 100 MB)。內嵌的圖片與影片較大時,先壓縮,或改用 YouTube 嵌入。

## 相關檔案

- 檢查腳本:`scripts/check_slides.py`
- 網站下載頁的產生:`scripts/build_docs.py`(`write_slides_index`)
- 投影片與講義的對應:`lectures/lecNN.md`、`schedule.md`


## 一個KP一個檔案（教師2026-10-16指定）

新增或重製的知識點教材，每個KP各自存成一份完整JianBauDau文件，講義也各自一份Markdown，兩者使用相同主檔名。例如 `lec03-kp02-batch-perceptron.md` 與 `lec03-kp02-batch-perceptron.jbd.json`。一份簡報內不得合併多個KP；該KP可有多個內容頁。
