"""KP08 deck (mini-batch and epoch), undergrad, 4-hour deck (12.5 min per KP), 4 pages."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))   # copy this file to your work dir; kit lives in view-from-text/tools/deckkit
sys.path.insert(0, os.environ.get("DECK_KIT", r"<skill>/tools/deckkit"))   # set env DECK_KIT to the deckkit folder
import kit  # noqa: E402
from kit import AUX, C, Card, Col, EDGE, Fig, MAIN, OK, REF, Row, T, Table, WARN, en  # noqa: E402

LEVEL_NOTE = "教材程度:大學生(undergrad)。簡報時長:4 小時(淨授課 200 分鐘,每 KP 12.5 分鐘,細度:精簡,每 KP 3–4 頁)。本 KP 共 4 頁。"


def bridge(key, zh, en_):
    return Card(key, T(zh, en(en_)), c=None, size=22, h=70)


def mbridge(p, key, zh, en_):
    h = p.need_h(key, 70)
    p.card(key, 60, 136, 1160, h, T(zh, en(en_)), c=None, size=22)
    return 136 + h + 14


def build():
    u = kit.Unit("u01", "小批次與 epoch", 0, 0)

    rows = [("批次大小", "每步成本", "雜訊", "硬體利用"),
            ("b = 1", "最低", "最大", "差"),
            ("1 < b < n", "中", "中", "好"),
            ("b = n", "最高", "零", "記憶體不足")]
    u.flow("單筆太吵,全批太慢", "單筆太吵、全批太慢,小批次是折衷", "A single example is too noisy and the full batch too slow; mini-batches compromise",
           "這一頁承接 KP07:單筆梯度雜訊太大。看三種批次大小。b 等於 1 就是 KP07 的 SGD:每步最便宜、雜訊最大,而且一次只算一筆,GPU 大部分閒著。b 等於 n 是完整梯度下降:沒有雜訊,但每步最貴,記憶體也常常裝不下。小批次取中間,每步隨機取 b 筆,常見 32 到 256,用這一批的平均梯度更新。"
           "好處有兩個:批次平均把方差壓低,而且 b 筆的運算可以打包成矩陣乘法並行。它仍是無偏的,均勻抽樣時期望等於完整梯度。上一頁(KP07)指出單筆太吵,這一頁給出折衷。接下來第二頁問:資料怎麼分、什麼叫一個 epoch?",
           bridge("p1bridge", "**KP07 留下的問題**:單筆太吵。**這頁問**:單筆與全批各有什麼問題?折衷怎麼取?",
                  "KP07 left a question: a single example is too noisy. What are the problems of the two extremes and how do we compromise?"),
           Table("p1t", rows, [260, 290, 290, 290], row_h=62, hdr_h=62, size=22, hl=2),
           C("p1c", T(r"**小批次**:$g_B(w)=\frac1{|B|}\sum_{i\in B}\nabla f_i(w)$,仍是無偏的,又能用 GPU 矩陣運算並行。", en("The batch average lowers the variance, and the batch can be computed in parallel as matrix operations.")), c=MAIN, size=22))

    # ---------------------------------------------------------------- page 2 (manual)
    p = u.page("洗牌、切批、用完一輪是一個 epoch", "洗牌後切成互斥批次,每批用一次叫一個 epoch", "Shuffle, cut into disjoint batches, and use each once: that is one epoch")
    y0 = mbridge(p, "p2bridge", "**上一頁**取了小批次。**這頁問**:資料怎麼分?什麼叫一個 epoch?",
                 "We chose mini-batches. How is the data cut, and what is an epoch?")
    specs = [("a", T("**資料** $\\mathcal D$", "$n=1000$ 筆", en("the training set")), REF, 60, 300),
             ("b", T("**洗牌後切批**", "$b=32$:31 個互斥批次", en("shuffle, then cut")), AUX, 440, 380),
             ("c", T("**逐批更新**", "31 次更新 = 1 個 epoch", en("each batch used once")), MAIN, 900, 320)]
    ha = max(p.need_h(k, 110) for k, _, _, _, _ in specs)
    ids = {}
    for k, tx, c, x, w_ in specs:
        ids[k] = p.card(k, x, y0, w_, ha, tx, c=c, size=22)
    p.conn(ids["a"], 4, ids["b"], 12)
    p.conn(ids["b"], 4, ids["c"], 12)
    h1 = p.need_h("d", 130)
    p.card("d", 60, y0 + ha + 36, 1160, h1, T("**剩 8 筆**:$31\\cdot32=992$。保留成較小的最後批次(32 次更新),或 drop_last=True 丟掉(31 次更新)。",
                                           "每個 epoch 開始前要**重新洗牌**。互斥:任兩批沒有共同樣本,一輪裡每筆恰好看一次。",
                                           en("Keep the 8 as a smaller last batch or drop them; reshuffle before every epoch.")), c=EDGE, size=22)
    p.step("這一頁回答資料怎麼分。標準做法是先把整個訓練集隨機洗牌,再依序切成 ⌊n/b⌋ 個大小為 b 的互斥批次,互斥的意思是任兩批沒有共同樣本,所以一輪裡每個樣本恰好被看過一次。把所有批次各用一次,叫一個 epoch。例子 n 是 1000、b 是 32:⌊1000/32⌋ 是 31 個完整批次,共 992 筆,剩 8 筆。"
           "剩下的可以保留成較小的最後批次,共 32 次更新,最後一批雜訊較大;或設 drop_last 為真丟掉,共 31 次更新,下一個 epoch 重新洗牌,丟掉的會換一批。有放回抽樣也存在,批次可以重疊,抽 n 次約 63.2 比例的獨特樣本被抽中。上一頁說要用小批次,這一頁說怎麼落實。接下來第三頁問:批次的估計有多準?")

    u.flow("批次估計有多準", "批次越大估計越準,無放回還有修正", "A larger batch estimates better, and sampling without replacement adds a correction",
           "這一頁用四筆資料算批次估計。在最小點,單筆梯度是 3、1、負 1、負 3,平均 0,σ 平方是 5。批次 {1,2} 的平均是 2,批次 {3,4} 是負 2,完整平均是 0:小批次的估計可以和完整梯度的方向相反,但平均起來是 0。六種兩筆批次的平均是 2、1、0、0、負 1、負 2,標準差 1.291;單筆是 2.236;全批是 0。"
           "公式:獨立抽樣方差是 σ 平方除以 b;無放回還要乘有限母體修正 n 減 b 除以 n 減 1。驗算 n 是 4、b 是 2:5 除以 2 乘 2/3 是 1.667,開根號 1.291,與六種平均一致。上一頁是怎麼分批,這一頁是準不準。接下來第四頁問:批次大小怎麼取捨?",
           bridge("p3bridge", "**上一頁**分好了批次。**這頁問**:一個批次的估計有多準?",
                  "The batches are cut. How accurate is the estimate from one batch?"),
           Row("p3r", [Col(520, [Fig("p3f", "lec03-kp08-batch-std", 520)]),
                       Col(640, [C("p3a", T(r"梯度 $3,1,-1,-3$:批次 $\{1,2\}\to2$,$\{3,4\}\to-2$,完整 $=0$。", en("A single batch can point opposite to the full gradient.")), c=REF, size=22),
                                 C("p3b", T(r"標準差:$b=1$ 為 $2.236$,$b=2$ 為 $1.291$,$b=4$ 為 $0$〔程式計算〕。", en("The standard deviation falls as the batch grows.")), c=AUX, size=22),
                                 C("p3c", T(r"無放回:$\mathrm{Var}=\frac{\sigma^2}{b}\cdot\frac{n-b}{n-1}$;$n=4,b=2$:$\frac52\cdot\frac23=1.667$。", en("Without replacement the finite-population correction applies.")), c=EDGE, size=22)])], gapx=40))

    u.flow("批次大小的取捨", "批次大小控制三件事,epoch 不是通用的算力單位", "Batch size controls three things, and an epoch is not a universal unit of compute",
           "最後整理取捨。批次大小控制三件事:雜訊,越大越小;記憶體,越大越吃;每個 epoch 的更新次數,floor n 除以 b,越大越少。沒有放諸四海皆準的最佳值。另外 epoch 不是通用的算力單位:訓練 10 個 epoch,在 n 是 1000 時 b 是 10 是 1000 次更新,b 是 100 只有 100 次更新。比較兩個訓練設定時,要同時看更新步數與看過的樣本總數。"
           "來源說單筆 SGD 的 GPU 利用率低於 5%,以及全批次容易收斂到尖銳極小值,前者沒有依據,後者有爭議,我們不採用,尖銳與平坦留給 KP12。上一頁看到批次越大越準,這一頁看到代價。接下來進入 KP09:有雜訊時,收斂到底是什麼意思?",
           bridge("p4bridge", "**上一頁**批次越大越準。**這頁問**:批次大小怎麼取捨?epoch 能不能當算力單位?",
                  "A larger batch is more accurate. How do we choose the batch size, and can an epoch measure compute?"),
           C("p4a", T("**三件事**:雜訊(越大越小)、記憶體(越大越吃)、每個 epoch 的更新次數 $\\lfloor n/b\\rfloor$(越大越少)。", en("Batch size controls noise, memory and the number of updates per epoch.")), c=REF, size=22),
           C("p4b", T("**epoch 不是通用算力單位**:$n=1000$、10 個 epoch:$b=10$ 是 1000 次更新,$b=100$ 只有 100 次。", en("Compare the number of updates and the number of examples seen, not only epochs.")), c=WARN, size=22),
           C("p4c", T("**留給 KP09**:有雜訊時,「收斂」到底是什麼意思?", en("Left for KP09: with noise present, what does convergence mean?")), c=MAIN, size=22))
    return [u]


if __name__ == "__main__":
    U = build()
    doc = kit.assemble(U, "課名 第N週 KPNN:標題(程度・時長)", [], {"x": 200, "y": 100, "zoom": 1.2, "rotation": 0})
    kit.steps[0]["speakerNotes"] = LEVEL_NOTE
    doc["steps"] = kit.steps
    out = os.path.join(HERE, "draft.jbd.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)
    print("pages", sum(1 for s in kit.steps if s["target"]["sceneId"] != "scene-root"), "KB", os.path.getsize(out) // 1024)
