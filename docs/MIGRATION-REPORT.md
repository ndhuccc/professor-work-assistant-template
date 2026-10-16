# 0.2.0 原始工作程序補齊報告

查核時間：2026-10-17 07:36（Asia/Taipei）。本報告是本機可審閱版本；遠端同步狀態另行核實。

## 變更結果

- 保留原課程七項技能全文與資源，含教材程度、敘事及盤點共通規範，共 315 個技能／支援檔。
- 保留原名稱 pr2026-course-assistant、review-graduate-research、mission-log，並將帳號、課程工作根目錄與私人目的地改為目前使用者設定。
- 13 組程序使用原始技能路由，六個舊通用名稱保留為轉接入口；共 19 個技能入口。
- 帶入簡報島 v3 格式規格、原 deckkit 與稽核器、JPEG 漫畫插頁程式、LabTube 六類契約及教師端查核工具。
- 提供新課程初始化、LabTube 本機驗證、來源雜湊檢查與自足 JBD 示範；不包含學生資料或正式資料庫。

## 來源

| 來源 | 固定版本 |
|---|---|
| ndhuccc/pr-2026-fall | 4c66c650c78f4eee6cadd24137e87b9be0841462 |
| ndhuccc/idl-2026-fall | fb7e2e363836674a8160576cb33bcc98cc5ae28e |
| ndhuccc/LabTube | 6080b9ce7acf706d48223b860d6f1ac1c7c0f727 |

340 個上游檔案逐一記錄來源、目的地與 Git blob SHA。原技能入口另存原文；啟用入口的 YAML 適配有額外雜湊。個人技能原文保留文字快照與 SHA-256，沒有把未取得的歷史附件稱為原件。

## 已執行驗證

| 項目 | 結果與範圍 |
|---|---|
| 技能 metadata | 19/19 通過原 quick_validate |
| 上游來源完整性 | 340/340 檔及三個個人技能入口快照通過 |
| 全部本機測試 | 20/20 通過；含初始化不覆寫、壞連結、來源竄改、別名錯誤及私人路徑防護 |
| 新課程工作副本 | 七項原技能與相依資源可複製至全新目錄 |
| 作業轉檔 | 合成 Markdown → 原轉檔器 → labtube.assignments.v1 → 原契約驗證通過 |
| 簡報產生 | 自足示例 → 原 deckkit → JBD v3 → 原 check_slides 通過 |
| 漫畫插頁 | 中性測試圖可嵌入真 JPEG；來源不變、頁序正確、視窗不重疊 |
| 測驗與評分格式 | 題目含答案欄位會拒絕；初評標示仍需正式伺服器核對 |
| 乾淨下載重現 | 從 Git 實際追蹤版本匯出並解壓，340 檔完整性、結構檢查與八項原流程測試再次通過 |

本測試使用合成資料；沒有執行學生程式、登入 LabTube、施測或提交成績。

## 適配、限制與已修復問題

1. 原 diagram-design YAML 的描述含冒號；所有課程入口已正規化 metadata，正文保留，原入口另保存。
2. 原 deckkit 必須有 figures registry。上游 example_deck.py 依賴特定課程圖資；另提供自足示例，使用空 figs.json，避免新下載者誤把它當作可直接執行範例。
3. 個人研究與紀錄技能的歷史 references 附件無法讀取；已依主技能明文建立可攜契約與模板，明確標示重建範圍。真實名冊與服務目的地必須由當前使用者提供。
4. 來源有不同授權；保留原授權與署名，詳 THIRD_PARTY_NOTICES。目標倉庫維持 Private，不改分享權限。
5. 實際生圖、中文圖像可讀性、瀏覽器目視、原生簡報島播放、正式 LabTube 匯入與帳號權限尚未實測；結構／格式通過不等於這些項目通過。
6. Git 下載可能轉換換行；已對上游資源設定保留原始位元組，避免跨平台 checkout 破壞來源雜湊。乾淨下載檢查已驗證此設定。

## 新使用者啟動方式

```sh
python scripts/bootstrap.py
python scripts/doctor.py --template --capabilities
python scripts/create_course.py --id DEMO --name Demo --demo
```

然後請 Agent 閱讀 AGENTS.md，選定剛建立的 course_root 與對應原技能執行。DEMO 目錄已存在時換新 ID，不覆寫原有工作。

## 待確認的外部更新

目標為 ndhuccc/professor-work-assistant-template，保持 Private 與 Template repository。本次不修改 PR、IDL、LabTube 或個人技能庫，不上傳學生或私人工作資料。
待使用者確認這份具體變更後，才推送本版本並讀回遠端 commit、檔案與倉庫設定。
