# 課程設定契約

讀取 config/project.local.json 的 courses 陣列。每課設定 id、name、repository、branch、local_root、state_file、timezone。
真正的 course_root 由已核實本機目錄決定；遠端 repo 是來源身分，不是可直接執行的磁碟路徑。
原作者課程可由使用者自行設定 PR 或 IDL，但新使用者不預設擁有任何帳號權限。
新課初始化使用 scripts/create_course.py；既有課程先讀其自己的規範，不能用範本規範靜默覆蓋。
正式課程 local_root 必須在範本及其他 Git 工作樹之外，以 --destination 明確指定；workspace/courses 僅限 --demo 合成試跑。先讀 docs/NEW-COURSE.md，建立後在課程目錄依 GITHUB_SETUP.md 分步設定 GitHub 與 Actions，核實後只更新本課設定，保留其他欄位。
