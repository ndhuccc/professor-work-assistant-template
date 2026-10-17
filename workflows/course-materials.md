# 教材製作：來源、講義、投影片與延伸教材

主要程序：W02、W03、W04、W05、W06。依請求選擇分支，無須每次製作全部形式。
先遵循 [AGENTS.md](../AGENTS.md) 與 [品質契約](../docs/QUALITY.md)。本文件負責串接，專業方法及細項驗收以各原技能為準。

## 觸發與範圍

- 「依這份 PDF／網址製作講義與簡報」：先 W02，再 W03。
- 「把這份簡報加入四格漫畫」：直接 W04，保留使用者提供的原簡報。
- 「畫圖解／做互動教材」：W05；「轉成自學指南／閱讀網頁」：W06。
- 已有講義或投影片時，讀取實際檔案後接續需要的階段，不重做已核准內容。
- 預設一個 KP 一份 Markdown 講義、一份可編輯簡報；另有批次索引。格式示例不代表正式教材已驗收。

## 必要輸入

1. 當次選定的課程與 `course_root`、來源文件／URL、章節／頁碼、已核准的教材程度與語言。
2. 需要的產物、KP 範圍、既有檔案與手動修改、簡報時長與細度、輸出位置及發布意圖。
3. 來源與插圖的實際可讀內容、授權／引用位置；PDF 公式需可核對畫面。缺頁、掃描文字或錯誤公式先列缺口，不猜測。
4. 需要的檔案處理、生圖、瀏覽器與原生播放器能力。工具缺失可先完成可做的草稿，分別記錄未執行驗證。

已有設定先讀取；課程或來源有歧義才詢問。新課程依 [可攜說明](../docs/PORTABILITY.md) 建立工作區；範例課號與日期不能作正式政策。

## 技能與工具

| 程序 | 必須讀取的技能 | 工具與相依資源 |
|---|---|---|
| W02 來源轉講義 | [textbook-lecture-notes](../.agents/skills/textbook-lecture-notes/SKILL.md) | 技能中的 audit_lecture.py、render_formula.py；共用 LEVELS、NARRATIVE、INVENTORY_FORMAT |
| W03 講義轉投影片 | [view-from-text](../.agents/skills/view-from-text/SKILL.md) | 原 v3 格式／設計／稽核文件、deckkit、audit_deck.py、preview_deck.py、course_root 的 scripts/check_slides.py |
| W04 四格漫畫 | [slides-to-four-panel-comics](../.agents/skills/slides-to-four-panel-comics/SKILL.md) | 原 JBD v3 插頁工具、實際生圖與圖像檢查能力；JPEG 編碼需 Pillow |
| W05 圖解與互動教材 | [diagram-design](../.agents/skills/diagram-design/SKILL.md) | 技能樣式門檻、類型參考、模板與 self_check.py；瀏覽器另驗證 |
| W06 自學／閱讀頁 | [self-study-web](../.agents/skills/self-study-web/SKILL.md) | 保留 Markdown 主檔；語意化 HTML、公式渲染與瀏覽器 |

課程根目錄中的原工具路徑以該課技能副本為準；下列 root 工具則從範本根目錄執行。兩者不要混用。

## 執行程序

1. 先用 [課程盤點](course-management.md) 選課並讀當前課程規範、進度與版本。辨認既有講義／簡報的真正格式，保留原檔與使用者手動修訂。
2. 讀取指定來源全文及必要畫面，建立來源 ID、版本、章節／頁碼、讀取狀態與圖表清單。以來源的定義、數值與邊界條件核對公式，遇到矛盾列出證據。
3. 依原共通規範提出章級與 KP 級知識地圖、因果鏈、程度、圖需求、覆蓋／取捨、分批計畫。W03 另列頁序銜接、語言、時長與細度。先交盤點／規劃審閱；當次已核准同一範圍則繼續。預設依序作業，不自動委派。
4. W02：以知識點重新講解來源，保留定義、推導、例子、迷思與小練習。依原規格處理雙語及圖說；補充材料標明來源。講義深度不因簡報時長而縮減。
5. W03：從已核准講義製作真正 PresentationDocumentV3，使用原規格與 deckkit。每 KP 頁數、鏡頭、圖覆蓋、講者備註及中英對照依原技能；備註也屬可公開內容。沒有圖資時按原工具初始化 figures registry；不直接執行依賴特定課程圖資的上游示例。
6. W05：在 W02／W03 需要圖解時即可進入此分支。依概念關係選圖型並遵守原技能的樣式確認。數值圖用可重現數據與計算；互動圖檢查初始狀態、參數變更、邊界條件及無 JavaScript／靜態狀態。按需嵌入講義／簡報，保留資料與圖的來源對應。
7. W04：建立核心觀念到原頁／step 的對照，每個核心觀念一張 16:9、2×2 四格漫畫。實際生成並逐圖檢查後，再用原工具插到對應內容的緊接次頁；JPEG 由原圖編碼，不能只改副檔名。維持原頁相對順序與整個 viewport 不重疊；缺生圖能力時交付分鏡與提示詞，停止插頁分支。
8. W06：以已有講義／簡報的實際內容串接自學因果鏈，加入思考與練習；閱讀頁保留標題、表格、連結、圖片與 LaTeX。保持 Markdown 主檔，另產生 HTML，測試桌面及手機。
9. 執行下述適用檢查，修正後只重跑受影響項目。漫畫版保留為原簡報的衍生版本；若新增插頁與原內容頁數或稽核規則衝突，列明並取得適用規格，不能靜默停用 FAIL 或沿用原版的通過結果。
10. 更新每 KP 產物清單、來源／圖片覆蓋、驗證紀錄與課程狀態草稿。發布接 [repo-maintenance](repo-maintenance.md) 的 W13；紀錄依其 W12，不能把本機完成寫成已上線。

### 已核對的工具用法

以下前三項在選定的 `course_root` 執行，檔名、程度與其他參數換成已核准值：

```sh
python .agents/skills/textbook-lecture-notes/scripts/audit_lecture.py lectures/lecNN-kpXX.md
python .agents/skills/view-from-text/tools/audit_deck.py slides/lecNN-kpXX.jbd.json --lecture lectures/lecNN-kpXX.md --speaker-notes
python scripts/check_slides.py slides/lecNN-kpXX.jbd.json
```

預覽另依原技能使用 preview_deck.py，輸出放暫存／指定工作目錄。漫畫工具路徑為所選技能副本的 scripts/insert_jbd_comics.py；它支援 JBD v3，PPTX／HTML 需各格式的可編輯工具。
新下載者可從範本根目錄先用 `python scripts/create_course.py --id DEMO --name Demo --demo` 建立合成示範，再按 [可攜說明](../docs/PORTABILITY.md) 執行 JBD 自足示例。這不會生成正式課程或生圖成果。

## 確認節點

- 來源範圍、程度、規劃及原技能要求的設計確認，集中已缺的決策；已有具體核准不重問。
- 使用者修改的原檔不得覆寫；重製與漫畫版使用新版本名稱，替換前確認差異。
- 安裝套件、發布、覆蓋遠端與分享依當前授權處理；原技能中的歷史授權不能代替本次授權。

## 輸出與驗收

- 每 KP 的來源對照、Markdown 講義、可編輯簡報及需要的圖資；選用漫畫／自學／HTML 衍生版另列。
- 知識／公式／數值／圖表覆蓋可追溯；一張圖的原始數據、程式與圖說互相對應。
- 原稽核器 FAIL 歸零；WARN 逐項處理或說明。字與字、圖、公式、按鈕、圖例無重疊、截切或溢出，縮放與動畫不漂移。
- 預覽是近似渲染；原生簡報島匯入、播放與匯出按原技能另驗證。缺工具就列未執行，不能宣稱已通過。
- 交付檔案路徑、適用程度、修改／未覆蓋項、檢查證據與下一步；考題答案及私人評語不混入公開教材。

## 失敗處理與交接

來源不可讀就標出範圍與可補資料；公式存疑就暫停受影響 KP 的定稿。圖資缺漏先列清單再修補，避免用近似圖冒充原數據。
格式錯誤保留錯誤訊息與檔案版本，修正後再稽核；缺播放器可交付明確標示的待驗草稿。交接保留已核准規劃、完成 KP、實際輸出位置、未決項與 W12 紀錄，不把重新執行當成查詢紀錄。
