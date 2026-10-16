# 示意圖配方(matplotlib → SVG)

本文件是 `VISUAL_AND_LAYOUT_GUIDE.md` §4 的實作配方。每一段程式碼都可以直接執行,結尾都會得到 `uri`(SVG data URI)。執行前請先 `py -m pip install -r requirements-lecture.txt`。

**何時必須用配方**:見 `SKILL.md` §4A 圖型對照表。講義中出現函數式、分布、幾何、決策邊界、門檻或面積時,該單元必須有對應的圖。不能只用公式代替。

**共通規則**
- 座標一律由公式計算,不手填點。函數曲線用 `np.linspace` 取至少 400 點。
- 圖內只放拉丁字母、數字與數學符號(`$…$` mathtext)。中文標註用原生 text 節點疊在圖上(`data_to_node`)。
- 方向、角度、垂直的圖一律加 `ax.set_aspect("equal")`。
- 不要用 `bbox_inches="tight"`。
- 顏色取自 `VISUAL_AND_LAYOUT_GUIDE.md` §2.1。
- 圖的寬高要與 image 節點寬高等比例(`new_figure(寬, 高)` 的寬高即節點像素)。

## R1 一維高斯密度(講義 §5.1)

```python
import numpy as np
from jbd_figure import *
use_jbd_style()

mu, sigma = 0.0, 1.0
fig, ax = new_figure(560, 400)
x = np.linspace(mu - 4 * sigma, mu + 4 * sigma, 400)
p = np.exp(-(x - mu) ** 2 / (2 * sigma ** 2)) / (np.sqrt(2 * np.pi) * sigma)
ax.plot(x, p, color="#6a9fd6", lw=2.5)
ax.fill_between(x, 0, p, color="#6a9fd6", alpha=0.12)
ax.axvline(mu, color="#e0995f", ls="--")
ax.set_xlim(-4, 4)
ax.set_ylim(0, 0.5)
ax.set_xlabel(r"$x$")
ax.set_ylabel(r"$p(x)$")
uri = svg_data_uri(fig)
```

## R2 二維高斯的等機率橢圓(講義 §5.2,說明 Σ 管形狀)

```python
import numpy as np
from jbd_figure import *
use_jbd_style()

mu = np.array([0.0, 0.0])
Sigma = np.array([[2.0, 1.2], [1.2, 1.0]])
fig, ax = new_figure(480, 480)
vals, vecs = np.linalg.eigh(Sigma)
t = np.linspace(0, 2 * np.pi, 400)
for k, alpha in [(1.0, 1.0), (2.0, 0.5)]:
    # 等機率線 (x-mu)^T Sigma^{-1} (x-mu) = k^2 是橢圓,軸長為 k*sqrt(特徵值)
    ell = vecs @ np.diag(np.sqrt(vals)) @ np.vstack([k * np.cos(t), k * np.sin(t)])
    ax.plot(mu[0] + ell[0], mu[1] + ell[1], color="#5fb8a8", lw=2.2, alpha=alpha)
ax.scatter([mu[0]], [mu[1]], color="#d97757", zorder=3)
ax.set_aspect("equal")
ax.set_xlim(-4, 4)
ax.set_ylim(-4, 4)
ax.set_xlabel(r"$x_1$")
ax.set_ylabel(r"$x_2$")
uri = svg_data_uri(fig)
```

## R3 兩類判別函數與決策邊界(講義 §5.3 的一維 QDA)

```python
import numpy as np
from jbd_figure import *
use_jbd_style()

def log_gauss(x, m, s):
    return -0.5 * ((x - m) / s) ** 2 - np.log(s) - 0.5 * np.log(2 * np.pi)

x = np.linspace(-6, 6, 800)
g1 = log_gauss(x, 0.0, 1.0) + np.log(0.5)
g2 = log_gauss(x, 2.0, 2.0) + np.log(0.5)
fig, ax = new_figure(560, 400)
ax.plot(x, g1, color="#6a9fd6", lw=2.5, label=r"$g_1(x)$")
ax.plot(x, g2, color="#d97757", lw=2.5, label=r"$g_2(x)$")
d = g1 - g2
for r in x[1:][np.sign(d[1:]) != np.sign(d[:-1])]:  # 兩條曲線的交點即決策邊界
    ax.axvline(r, color="#e0995f", ls="--")
ax.set_xlim(-6, 6)
ax.set_xlabel(r"$x$")
ax.legend(loc="lower left", frameon=False)
uri = svg_data_uri(fig)
```

## R4 誤判陰影與門檻(講義 §2)

```python
import numpy as np
from jbd_figure import *
use_jbd_style()

def pdf(x, m, s):
    return np.exp(-(x - m) ** 2 / (2 * s * s)) / (np.sqrt(2 * np.pi) * s)

x = np.linspace(-4, 4, 800)
w1 = 0.5 * pdf(x, -1.0, 1.0)   # 加權密度 P(w1) p(x|w1)
w2 = 0.5 * pdf(x, 1.0, 1.0)    # 加權密度 P(w2) p(x|w2)
x0 = 0.0
fig, ax = new_figure(560, 400)
ax.plot(x, w1, color="#6a9fd6", lw=2.5)
ax.plot(x, w2, color="#d97757", lw=2.5)
left = x <= x0
right = x >= x0
ax.fill_between(x[left], 0, w2[left], color="#d97757", alpha=0.25)   # w2 誤判為 w1
ax.fill_between(x[right], 0, w1[right], color="#6a9fd6", alpha=0.25)  # w1 誤判為 w2
ax.axvline(x0, color="#e0995f", ls="--")
ax.set_xlim(-4, 4)
ax.set_ylim(0, 0.25)
ax.set_xlabel(r"$x$")
uri = svg_data_uri(fig)
```

## R5 統計圖(直方圖,固定亂數種子並在圖說標示 n)

```python
import numpy as np
from jbd_figure import *
use_jbd_style()

rng = np.random.default_rng(0)
a = rng.normal(-1.0, 1.0, 300)
b = rng.normal(1.0, 1.0, 300)
fig, ax = new_figure(480, 400)
ax.hist(a, bins=25, density=True, color="#6a9fd6", alpha=0.5)
ax.hist(b, bins=25, density=True, color="#d97757", alpha=0.5)
ax.set_xlabel(r"$x$")
ax.set_ylabel("density")
uri = svg_data_uri(fig)
```

## R6 判別差 g(x)=g1(x)-g2(x) 與決策邊界(講義 §4 決策曲面、§5.3)

```python
import numpy as np
from jbd_figure import *
use_jbd_style()

def log_gauss(x, m, s):
    return -0.5 * ((x - m) / s) ** 2 - np.log(s) - 0.5 * np.log(2 * np.pi)

x = np.linspace(-6, 6, 800)
# 與 R3 相同的一維例子;等先驗時 ln(0.5) 相消,g = g1 - g2
d = log_gauss(x, 0.0, 1.0) - log_gauss(x, 2.0, 2.0)
fig, ax = new_figure(560, 400)
ax.plot(x, d, color="#5fb8a8", lw=2.5)
ax.fill_between(x, 0, d, where=d > 0, color="#6a9fd6", alpha=0.25)   # g>0 判為 w1
ax.fill_between(x, 0, d, where=d < 0, color="#d97757", alpha=0.25)   # g<0 判為 w2
ax.axhline(0, color="#b7b0a5", lw=1)
for r in x[1:][np.sign(d[1:]) != np.sign(d[:-1])]:   # 零點即決策邊界
    ax.axvline(r, color="#e0995f", ls="--")
ax.set_xlim(-6, 6)
ax.set_xlabel(r"$x$")
ax.set_ylabel(r"$g(x)$")
uri = svg_data_uri(fig)
```

## 把 uri 放進節點

```python
from jbd_figure import image_node
node = image_node("lec02-u06-fig1", "一維高斯曲線", 60, 130, 560, 400, uri,
                  alt="一維高斯密度曲線,中心在 0,寬度 σ=1,中心虛線標示均值")
node["sceneId"] = "lec02-scene-u06"   # 必須改成實際子 Scene,不能留 placeholder
```

`alt` 要描述圖「顯示了什麼」,不寫「示意圖」。節點寬高比要等於 `new_figure` 的寬高比。
