# 課程盤點、課務維護與學期封存

主要程序：W01。先遵循 [AGENTS.md](../AGENTS.md) 與 [可攜執行說明](../docs/PORTABILITY.md)。

## 觸發與範圍

「目前教材到哪個 KP」「盤點課程進度」「建立新課程工作區」「調整時程／公告」「整理學期封存」。
先辨認盤點、新課初始化、政策草稿或發布／封存分支；僅詢問狀態時維持唯讀，不自行製作或發布教材。

## 必要輸入

課程選擇、設定中的 Repo／分支／course_root、查核時間與範圍、正式課綱／時程／政策及當次要求。
既有課程重用有效選擇；同時出現不同課程且有歧義才問課程。新課另需使用者自己的代號、名稱、正式網站位置及後續規準，示範值不得當作正式設定。

## 技能與工具

主要讀 [pr2026-course-assistant](../.agents/skills/pr2026-course-assistant/SKILL.md)。教材接 [course-materials](course-materials.md)，作業接 [assignment-labtube](assignment-labtube.md)；行政來源依 [admin-documents](admin-documents.md)。
紀錄使用 [mission-log](../.agents/skills/mission-log/SKILL.md)，發布與封存外部更動使用 [repo-publish](../.agents/skills/repo-publish/SKILL.md) 及 [repo-maintenance](repo-maintenance.md)。
初始化用範本 [bootstrap.py](../scripts/bootstrap.py)、[create_course.py](../scripts/create_course.py)，它們不建立遠端倉庫或正式學生資料。工具是否安裝與外部授權分開查核。

## 執行程序

1. 讀本機設定（若有），確認目前課程與 `course_root`。對既有課程讀其最新 AGENTS、COURSE_STATE、schedule、syllabus 與技能，不以範本舊快照當作該課現況。
2. 新課分支先讀 [設定說明](../docs/SETUP.md) 及 [獨立課程建立指南](../docs/NEW-COURSE.md)。引導使用者選本專案及其他 Git 工作樹之外的新目錄；建議與本專案同層，已有明確選擇就沿用。從範本根目錄執行：

   ```sh
   python scripts/bootstrap.py
   python scripts/doctor.py
   python scripts/create_course.py --id YOUR-COURSE --name "課程名稱" --destination ../YOUR-COURSE
   ```

   讀回實際 course_root；目錄已存在就保留並改新目的地，不覆寫。正式課程必填 --destination，範本內及其他 Git 工作樹內的路徑會被拒絕。正式日期、評分、授權及 example.invalid 網址仍待設定；工具不初始化 Git、不建立遠端。只有明確 --demo 的合成試跑才可放 workspace/courses/，不得藉此繞過正式課程限制。

   接著切到新課程目錄，讀取其 GITHUB_SETUP.md，結合 W13 逐步引導：本機建置與審閱 → 獨立 Git 與初始提交 → 空白 GitHub Repo → 遠端及推送 → 同一 commit 的 Course checks → 選用 Pages。新骨架內含可建置的網站、推送檢查與手動部署 workflow。每階段讀回驗證再繼續；缺資訊只問當前步驟所需項目，缺外部授權先完成本機成果，不自行發布。最後把已核實路徑與遠端寫回本機設定。
3. 盤點分支建立「單元／KP → 來源 → 講義 → 簡報 → 圖資 → 衍生版 → 稽核 → 發布」清單。依實際檔案、圖連結、測試紀錄與遠端版本判斷狀態，不只依 COURSE_STATE 的自述。
4. 分別標示未開始、草稿、待補圖、待審、檢查通過、目視待驗、已提交、已部署及阻礙。檔案存在不代表已驗收；遠端 commit 存在不代表網站已更新。
5. 修改時程／課綱／公告時，先找正式日期來源、假日、作業與考試依賴，列出受影響的項目、時區與學生可見內容。缺正式決定只產生草稿，不代訂期限、分組或配分。
6. 教材、作業、考試／專題需求分派到對應流程，帶入當次課程、來源與已核准決定；保持每 KP 獨立檔，不能跨課混用名冊、日期、網址或模板。
7. 課程工作區的原 scripts/doctor.py、build_docs.py、導覽與網站建置僅依本課規範使用；它們與範本 scripts/doctor.py 用途不同。先檢查實際 `--help` 及設定，不用範本結構 PASS 宣稱網站已建置。
8. 維護 COURSE_STATE／CHANGELOG／schedule 的任務相關草稿與證據連結；通過內容與相依檢查後走 W13 的外部發布及讀回，並以 W12 保存查核時間、未決項與位置。
9. 封存分支整理已核准版本、教材／圖資／依賴、來源授權、未結事項與恢復方式，先產生唯讀封存清單。關閉服務、改可見度、刪除資料、移除權限或定案成績都需各自具體核准，不能以學期結束自動執行。

## 確認節點

課程歧義、正式政策及日期衝突先問受影響的決策；既有資料能回答就不重問。
僅盤點與可逆草稿在授權範圍內進行；公開公告、推送、課務設定及封存外部動作須有對象、內容、影響與當前授權。原課程文件中的歷史授權不是新使用者的授權。

## 輸出與驗收

- 課程／分支／版本及查核時間明確，所有要求的單元／KP 均列狀態與證據。
- 正式新課位於範本與其他 Git 工作樹外，七項原技能、支援資源、網站骨架、GITHUB_SETUP.md 與 Actions workflow 完整；示範模式明確區分。Git、遠端、Actions、Pages 及目視各自有狀態與證據，無原作者帳號／日期預設。
- 課務草稿前後差異、影響清單及必要決策完整；已更新來源與課程狀態互相一致。
- 發布與封存狀態有對應讀回證據；本次未建置、未目視或未部署的項目明列。

## 失敗處理與交接

設定與實際 Repo 不符時保留雙方來源並核對，不能靜默切換分支或推測課程。原檔或使用者未提交修改先保存，不清除以便自動化。
圖資缺漏或版本落後則列出確切 KP、檔案與阻礙，交給對應流程處理。交接包含選定課程、course_root、版本、正式決定、完成／未完成清單及下一個可執行步驟。
