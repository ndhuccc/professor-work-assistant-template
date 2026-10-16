# 課程設定契約

讀取 config/project.local.json 的 courses 陣列。每課設定 id、name、repository、branch、local_root、state_file、timezone。
真正的 course_root 由已核實本機目錄決定；遠端 repo 是來源身分，不是可直接執行的磁碟路徑。
原作者課程可由使用者自行設定 PR 或 IDL，但新使用者不預設擁有任何帳號權限。
新課初始化使用 scripts/create_course.py；既有課程先讀其自己的規範，不能用範本規範靜默覆蓋。
