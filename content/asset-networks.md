---
title: "เครือข่ายสินทรัพย์: อ่านความสัมพันธ์ก่อนเลือกพอร์ต"
description: เริ่มจาก correlation กับ conditional dependence คำนวณ precision และ partial correlation เรียน Graphical Lasso การเลือก penalty ตามเวลา และอ่านภาพเครือข่ายอย่างมีขอบเขต
---

# เครือข่ายสินทรัพย์: อ่านความสัมพันธ์ก่อนเลือกพอร์ต

<p class="lead">หุ้นสองตัวอาจขึ้นลงด้วยกันเพราะรับแรงจากตัวแปรเดียวกัน เครือข่ายแบบ Gaussian ช่วยตรวจว่าความสัมพันธ์เชิงเส้นระหว่างคู่นั้นยังเหลืออยู่เท่าไรเมื่อควบคุมตัวแปรอื่นในชุดข้อมูลแล้ว</p>

กราฟเครือข่ายมี node แทนสินทรัพย์และ edge แทนความสัมพันธ์ที่เราเลือกนิยาม ถ้าวาดเส้นทุกคู่ที่ correlation สูง ภาพจะบอกความสัมพันธ์แบบคู่ต่อคู่ แต่ Graphical Lasso ประมาณเครือข่ายอีกชนิดหนึ่ง โดยใช้ inverse covariance หรือ precision matrix เพื่อดูความสัมพันธ์หลังควบคุมตัวแปรอื่นทั้งหมดที่รวมอยู่ในแบบจำลอง

เราจะเริ่มจากสามตัวแปรที่คำนวณด้วยมือได้ แล้วใช้ข้อมูลจำลองหกสินทรัพย์จาก [PCA](pca-diversification.html) และ [การจัดกลุ่มสินทรัพย์](asset-clustering.html) หน้านี้รันแยกจากบทก่อนหน้าได้ด้วย NumPy, pandas, SciPy และ scikit-learn ตัวอย่างไม่ได้ใช้ราคาตลาดหรือจำลองผลตอบแทนจาก Lab ของคอร์ส

บท [Graphical analysis](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/qhGsr/graphical-analysis) เชื่อม precision กับ conditional dependence ส่วน [Selecting a portfolio of assets](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/Nhqjd/selecting-a-portfolio-of-assets) และ [Lab Graphical Network Analysis](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/2vcIt/lab-session-graphical-network-analysis) นำไปใช้ร่วมกับการเลือกสินทรัพย์ การจัดกลุ่ม และการแสดงภาพ เราจะตรวจแต่ละขั้นแยกกันก่อนใช้กับพอร์ต

<span id="conditional-correlation-example"></span>

## สองตัวแปรขึ้นลงร่วมกันโดยผ่านตัวแปรที่สาม

ให้ $Z,\varepsilon_X,\varepsilon_Y$ เป็นตัวแปร Normal มาตรฐานที่เป็นอิสระกัน และกำหนด

$$X=0.8Z+0.6\varepsilon_X,\qquad
Y=0.6Z+0.8\varepsilon_Y.$$

ทั้ง X และ Y มี variance หนึ่ง เพราะ $0.8^2+0.6^2=1$ ทั้งคู่สัมพันธ์กับ Z แต่ส่วนที่เหลือหลังรู้ Z เป็น $0.6\varepsilon_X$ กับ $0.8\varepsilon_Y$ ซึ่งเป็นอิสระกัน

Correlation ของ X/Y เท่ากับ $0.8\times0.6=0.48$ จึงเห็นการเคลื่อนไหวร่วมกันหากดูสองคอลัมน์นี้ลำพัง เมื่อควบคุม Z แล้ว covariance ของส่วนที่เหลือเป็น $0.48-(0.8)(0.6)=0$ ตัวอย่างนี้แสดงว่า marginal correlation กับ conditional correlation เป็นคนละค่า

ถ้า $K=\Sigma^{-1}$ เป็น precision matrix ค่า partial correlation ของตัวแปร $i,j$ เมื่อควบคุมตัวอื่นทั้งหมดเขียนได้ว่า

$$\rho_{ij\mid\text{others}}=-\frac{K_{ij}}{\sqrt{K_{ii}K_{jj}}},\qquad i\ne j.$$

ต้องมีทั้งเครื่องหมายลบและการหารด้วยรากของค่าแนวทแยง การอ่าน $K_{ij}$ เป็น correlation ตรง ๆ จะให้เครื่องหมายและสเกลผิดได้

```python
import numpy as np
import pandas as pd

# รูปแบบตัวเลขที่แสดงผล ไม่ลดความละเอียดของค่าที่คำนวณ
np.set_printoptions(precision=6, suppress=True)
import warnings
from sklearn.covariance import GraphicalLasso
from sklearn.cluster import AffinityPropagation
from sklearn.exceptions import ConvergenceWarning
from scipy.spatial.distance import pdist, squareform

three_corr = np.array([[1., .8, .6], [.8, 1., .48], [.6, .48, 1.]])
three_precision = np.linalg.inv(three_corr)
def partial_correlations(precision):
    p = np.asarray(precision, dtype=float)
    out = -p / np.sqrt(np.outer(np.diag(p), np.diag(p)))
    np.fill_diagonal(out, 1.)
    return out

three_partial = partial_correlations(three_precision)
print('Marginal correlation X/Y:', three_corr[1, 2])
print('Partial correlation X/Y given Z:', three_partial[1, 2])
print('Conditional residual covariance:', .48 - .8 * .6)
```

เรียงตัวแปรใน `three_corr` เป็น Z, X, Y ผล marginal correlation X/Y คือ 0.48 ส่วน partial correlation X/Y given Z เป็นศูนย์ ในแบบจำลองร่วม Gaussian นี้ $K_{XY}=0$ เทียบเท่ากับ X และ Y เป็นอิสระกันเมื่อกำหนด Z แล้ว

สำหรับข้อมูลทั่วไป partial correlation ศูนย์หมายถึงความสัมพันธ์เชิงเส้นของ residuals เป็นศูนย์ ยังไม่เพียงพอที่จะสรุป conditional independence กราฟแบบไม่มีทิศทางนี้ยังไม่บอกว่าตัวแปรไหนเป็นสาเหตุของอีกตัว และการละตัวแปรออกจากชุดที่ควบคุมอาจเปลี่ยนความหมายของเส้นได้

<span id="network-teaching-data"></span>

## เตรียมข้อมูลฝึกโดยยังไม่เปิดช่วงท้าย

เราจะใช้ 260 สัปดาห์จาก Gaussian ที่พารามิเตอร์คงที่ แยกสัปดาห์ 1–208 เป็น training และ 209–260 เป็น test เมทริกซ์ที่สร้างไว้ให้ความสัมพันธ์โดยตรงตามแบบจำลองเป็นสาย A–B–C–D–E–F ส่วน correlation คู่ที่อยู่ไกลกว่านั้นยังอาจไม่เป็นศูนย์ เพราะผลของความสัมพันธ์ส่งผ่านตัวแปรกลางในโครงสร้างร่วม

```python
assets = np.array(list('ABCDEF'))
true_precision = np.eye(6)
for i, j, value in [(0, 1, -.55), (1, 2, -.20), (2, 3, -.45),
                    (3, 4, -.15), (4, 5, -.50)]:
    true_precision[i, j] = true_precision[j, i] = value
base_cov = np.linalg.inv(true_precision)
true_corr = base_cov / np.sqrt(np.outer(np.diag(base_cov), np.diag(base_cov)))
weekly_sd = np.array([.025, .030, .020, .022, .035, .028])
true_cov = true_corr * np.outer(weekly_sd, weekly_sd)
rng = np.random.default_rng(317)
returns = pd.DataFrame(
    .001 + rng.standard_normal((260, 6)) @ np.linalg.cholesky(true_cov).T,
    index=pd.RangeIndex(1, 261, name='Week'), columns=assets
)
train = returns.iloc[:208].copy()
test = returns.iloc[208:].copy()
print('Train/Test:', train.shape, test.shape)
print(train.head(3).round(4))
```

`true_precision` เป็น precision ก่อนปรับหน่วย SD เมื่อแปลง covariance ให้สินทรัพย์มี SD ต่างกัน ค่า precision จะเปลี่ยนสเกล แต่ตำแหน่งที่เป็นศูนย์และ partial correlations ยังคงเดิม ทุกตัวมีค่าเฉลี่ยตามแบบจำลอง 0.1% ต่อสัปดาห์ ใช้ seed 317 หนึ่งค่าและไม่ค้นหา seed ที่ทำให้วิธีเลือกพอร์ตดูชนะ

ข้อมูลที่มีจริงต้องแยก simple returns ออกจากราคาหรือผลต่างราคา และจัดวันที่ของทุกสินทรัพย์ให้ตรงกัน Lab ใช้ผลตอบแทนรายวันจาก CRSP และแปลงเป็นรายสัปดาห์ หากจะทำเช่นนั้น ผลตอบแทนสัปดาห์คือ $\prod_{d\in\text{week}}(1+r_d)-1$ ไม่ใช่บวกเปอร์เซ็นต์รายวันอย่างเดียว อัตรา T-bill ที่เสนอเป็น yield ต่อปีก็ยังไม่ใช่ realized return รายสัปดาห์ ต้องอ่าน convention ของ series ก่อนแปลงหน่วย

<span id="sample-precision"></span>

## ประมาณ precision จากข้อมูลตัวอย่าง

เพื่อให้ penalty มีสเกลใกล้กันทุกสินทรัพย์ เราจะหัก mean และหาร SD ที่เรียนจาก training เท่านั้น รอบนี้ใช้ `ddof=0` ให้ตรงกับ empirical covariance แบบหาร $T$ ที่ Graphical Lasso ใช้ จึงได้ข้อมูล $Z$ และ

$$S=\frac{Z^\top Z}{T},\qquad K_{\text{sample}}=S^{-1}.$$

การใช้ตัวหาร $T$ หรือ $T-1$ ต้องสอดคล้องกับการปรับหน่วย ถ้าหาร SD แบบ `ddof=1` แต่คำนวณ covariance หาร $T$ แนวทแยงจะเป็น $(T-1)/T$ แทนหนึ่ง แม้ความต่างจะเล็กเมื่อ T มาก แต่ penalty ที่ใช้กับเมทริกซ์ก็มีสเกลต่างตามไปด้วย

```python
train_mean = train.mean().to_numpy()
train_sd = train.std(ddof=0).to_numpy()
standardized = (train.to_numpy() - train_mean) / train_sd
empirical_corr = standardized.T @ standardized / len(train)
sample_precision = np.linalg.inv(empirical_corr)
sample_partial = partial_correlations(sample_precision)
print('Smallest covariance eigenvalue:', np.linalg.eigvalsh(empirical_corr).min())
print(pd.DataFrame(sample_partial, index=assets, columns=assets).round(3))
```

Eigenvalue ต่ำสุดประมาณ 0.368468 จึงกลับเมทริกซ์ตัวอย่างนี้ได้ ตาราง partial correlation จาก sample precision มีค่าที่ไม่เป็นศูนย์หลายคู่ แม้แบบจำลองประชากรที่สร้างข้อมูลมีเพียงห้าเส้น ข้อมูลสุ่มจำนวนจำกัดทำให้ค่าประมาณคลาดจาก covariance ประชากร เรียกความคลาดเคลื่อนนี้ว่า estimation noise

ในงานที่มีตัวแปรมากกว่า observations covariance แบบธรรมดามัก singular และกลับไม่ได้ บท [Covariance estimation](covariance-estimation.html) อธิบายปัญหานี้ไว้แล้ว Graphical Lasso เป็นวิธีหนึ่งที่เพิ่มโครงสร้างและ penalty ในการประมาณ แทนการตัดช่องของ inverse covariance ทีละช่องภายหลัง ซึ่งอาจทำให้ความเป็น positive definite เสียไป

<span id="graphical-lasso-objective"></span>

## Graphical Lasso ลงโทษเส้นที่เพิ่มความซับซ้อน

Graphical Lasso ประมาณ precision $K$ ด้วยโจทย์ convex บนเมทริกซ์ positive definite

$$\widehat K=\arg\min_{K\succ0}
\left\{\operatorname{tr}(SK)-\log\det K
+\alpha\sum_{i\ne j}|K_{ij}|\right\}.$$

สองพจน์แรกมาจาก Gaussian likelihood ส่วนพจน์สุดท้ายลงโทษขนาดสัมบูรณ์ของช่องนอกแนวทแยง ทำให้บางช่องเป็นศูนย์ `alpha` คือความแรงของ penalty: มากขึ้นหมายถึงลงโทษความซับซ้อนแรงขึ้น จึงมักได้กราฟที่บางลง แต่ไม่ได้พิสูจน์ว่าเส้นที่เหลือเป็นความสัมพันธ์จริง

`trace` คือผลรวมแนวทแยง และ `det` คือ determinant ของเมทริกซ์ เงื่อนไข $K\succ0$ ทำให้ inverse เป็น covariance ที่ใช้ได้ เราไม่ต้องเขียน optimizer เองในบทนี้ แต่ต้องตรวจว่าการคำนวณลู่เข้าและได้เมทริกซ์ที่มีสมบัติตามต้องการ [scikit-learn: sparse inverse covariance](https://scikit-learn.org/stable/modules/covariance.html#sparse-inverse-covariance)

```python
def fit_graph(x, alpha):
    with warnings.catch_warnings():
        warnings.simplefilter('error', ConvergenceWarning)
        model = GraphicalLasso(alpha=alpha, max_iter=1000, tol=1e-7).fit(x)
    if not np.isfinite(model.precision_).all():
        raise RuntimeError('Non-finite precision estimate')
    np.linalg.cholesky(model.precision_)
    return model

def edge_mask(precision, tolerance=1e-8):
    mask = np.abs(partial_correlations(precision)) > tolerance
    np.fill_diagonal(mask, False)
    return mask

alphas = np.array([.02, .08, .20, .60])
path_models = [fit_graph(standardized, alpha) for alpha in alphas]
edge_counts = [int(np.triu(edge_mask(model.precision_), 1).sum()) for model in path_models]
print(pd.DataFrame({'alpha': alphas, 'edges': edge_counts}))
```

สำหรับ alpha 0.02, 0.08, 0.20 และ 0.60 ได้ 11, 7, 4 และ 0 edges ตามลำดับ นับเฉพาะครึ่งบนเพื่อไม่ให้นับ A/B กับ B/A ซ้ำ ช่องแนวทแยงไม่ได้เป็นเส้นที่หุ้นเชื่อมกับตัวเอง ส่วน tolerance $10^{-8}$ ใช้แยกค่าศูนย์เชิงตัวเลข ไม่ใช่ threshold ทดสอบนัยสำคัญทางสถิติ

`ConvergenceWarning` ถูกเปลี่ยนเป็นข้อผิดพลาดเพื่อไม่ใช้ผลที่ยังไม่นิ่ง `np.linalg.cholesky` ตรวจ positive definiteness เพิ่ม ถ้าเกิดข้อผิดพลาดควรตรวจข้อมูลและการตั้งค่า ไม่ควรเพียงซ่อน warning แล้วอ่านเส้นต่อ

ที่ alpha 0.60 ทุก node แยกจากกันทั้งที่เรารู้ว่ากระบวนการสุ่มมีห้าเส้น การเพิ่ม penalty จนได้หุ้น “ดูเป็นอิสระ” จำนวนที่ต้องการจึงไม่ได้ทำให้หุ้นในประชากรเป็นอิสระตามรูป ภาพเปลี่ยนเพราะเราเพิ่ม regularization

<span id="graph-chronological-validation"></span>

## เลือก penalty โดยให้การตรวจเดินตามเวลา

Lab แนะนำ `GraphicalLassoCV` ซึ่งเลือก penalty ด้วย cross-validation แต่สำหรับการตัดสินใจตามเวลา เราต้องรู้ว่าแต่ละ fold ใช้อดีตส่วนใดฝึกและส่วนใดตรวจ โค้ดนี้เขียนขั้นตอนเองให้เห็นชัด โดยยังไม่ใช้ test 52 สัปดาห์ท้าย

| Fold | สัปดาห์ที่ใช้ฝึก | สัปดาห์ที่ใช้ validation |
|---|---|---|
| 1 | 1–104 | 105–130 |
| 2 | 1–130 | 131–156 |
| 3 | 1–156 | 157–182 |
| 4 | 1–182 | 183–208 |

ในแต่ละ fold ต้องเรียน mean และ SD จากส่วนฝึกของ fold นั้นด้วย การ standardize ทั้ง 208 สัปดาห์ก่อนแบ่ง fold จะทำให้ช่วง validation มีส่วนกำหนดสเกลของอดีต แม้ตัว estimator จะ fit เฉพาะแถวฝึกแล้วก็ตาม

```python
folds = [(104, 130), (130, 156), (156, 182), (182, 208)]
validation_scores = np.empty((len(folds), len(alphas)))
for fold, (cutoff, end) in enumerate(folds):
    earlier = train.iloc[:cutoff].to_numpy()
    later = train.iloc[cutoff:end].to_numpy()
    fold_mean, fold_sd = earlier.mean(axis=0), earlier.std(axis=0, ddof=0)
    x_earlier = (earlier - fold_mean) / fold_sd
    x_later = (later - fold_mean) / fold_sd
    for j, alpha in enumerate(alphas):
        validation_scores[fold, j] = fit_graph(x_earlier, alpha).score(x_later)
mean_scores = validation_scores.mean(axis=0)
chosen_alpha = float(alphas[np.argmax(mean_scores)])
print(pd.DataFrame({'alpha': alphas, 'Mean validation log-likelihood': mean_scores}).round(5))
print('Chosen alpha:', chosen_alpha)
```

`score` คืนค่าเฉลี่ย Gaussian log-likelihood ของข้อมูล validation ภายใต้โมเดลที่ fit ไว้ ค่าสูงกว่าดีกว่าในเกณฑ์นี้ ไม่ใช่ Sharpe ratio หรือกำไรที่คาดว่าจะได้ แต่ละ fold มี 26 สัปดาห์ จึงเฉลี่ยคะแนน fold เท่ากันได้

คะแนนของ alpha 0.02 ประมาณ −8.24646 สูงกว่า −8.25826 ของ 0.08 เล็กน้อย จึงเลือก 0.02 จากสี่ตัวเลือกนี้ แล้ว fit ใหม่ด้วย training 208 สัปดาห์ทั้งหมด ความต่างคะแนนเล็กยังอาจสะท้อนความไม่แน่นอนในการเลือกพารามิเตอร์ได้ และ likelihood ที่ดีกว่าไม่ได้รับรองว่าจะเลือกเส้นจริงครบหรือให้พอร์ตลงทุนที่ดีกว่า

ข้อมูลจำลองเป็น IID จึงไม่มี autocorrelation ที่ต้องเว้น gap ในตัวอย่างนี้ ข้อมูลจริงที่ใช้ overlapping returns หรือ features ที่มีช่วงเวลาเหลื่อมกันอาจต้องเว้นช่วงระหว่างฝึกกับตรวจเพิ่มเติม กฎแบ่งต้องสอดคล้องกับเวลาที่ข้อมูลทราบได้

<span id="partial-correlation-network"></span>

## อ่านน้ำหนักของ edge ในหน่วย correlation

หลังเลือก alpha แล้ว เราประมาณ precision จากข้อมูลฝึกทั้งหมด แปลงเป็น partial correlation และจัดตารางเส้น การดูตารางช่วยให้ตรวจทั้งเครื่องหมายและขนาดได้ก่อนวาดภาพ

```python
graph_model = fit_graph(standardized, chosen_alpha)
precision = graph_model.precision_
partial = partial_correlations(precision)
adjacency = edge_mask(precision)
edge_rows = []
for i in range(6):
    for j in range(i + 1, 6):
        if adjacency[i, j]:
            edge_rows.append({'From': assets[i], 'To': assets[j],
                              'Partial correlation': partial[i, j]})
edge_table = pd.DataFrame(edge_rows)
print(edge_table.round(4).to_string(index=False))
print('Covariance inverse check:', np.allclose(graph_model.covariance_ @ precision, np.eye(6), atol=1e-6))
```

คู่ A/B มี partial correlation ประมาณ 0.5411, C/D ประมาณ 0.4710 และ E/F ประมาณ 0.4255 ขณะที่ A/E ประมาณ −0.1115 ภายใต้เมทริกซ์ประมาณนี้ เส้นติดลบจึงต้องแสดงเครื่องหมายด้วย ไม่ควรใช้ความหนาของเส้นอย่างเดียวแล้วทำให้ผู้อ่านคิดว่าทุกเส้นเป็นความสัมพันธ์บวก

โมเดลที่เลือกมี 11 เส้น มากกว่าห้าเส้นของกระบวนการสุ่มจริง เรารู้ความต่างนี้ได้เพราะเป็นข้อมูลจำลอง ในข้อมูลตลาดไม่มี `true_precision` ให้เทียบ จึงต้องประเมินความไวต่อช่วงเวลาและการตั้งค่าเพิ่ม การไม่เห็นเส้นบน estimated graph ยังไม่ใช่หลักฐานว่าความสัมพันธ์ไม่มีในตลาด

<figure class="lesson-figure">
<picture>
<source media="(max-width: 520px)" srcset="assets/charts/ml-partial-correlation-mobile.svg">
<img src="assets/charts/ml-partial-correlation.svg" alt="ตาราง partial correlations ที่ประมาณจาก A–F โดย Graphical Lasso alpha 0.02 พร้อมตัวเลขและเครื่องหมายทุกคู่" loading="lazy" width="720" height="560">
</picture>
<figcaption>ข้อมูลจำลอง seed 317 จำนวน 208 สัปดาห์ ค่า alpha 0.02 มาจาก validation ตามเวลา สีแสดงเครื่องหมายและความเข้มสัมพันธ์กับขนาดสัมบูรณ์ อ่านตัวเลขประกอบเสมอ ค่าศูนย์หมายถึงศูนย์ของเมทริกซ์ประมาณภายใต้ penalty ที่เลือก</figcaption>
</figure>

กราฟนี้ไม่มีการชี้ทิศทางและไม่ได้ควบคุมทุกตัวแปรในเศรษฐกิจ คำว่า “others” ใน partial correlation หมายถึงอีกสี่สินทรัพย์ในชุด A–F เท่านั้น ไม่ได้หมายถึงกำจัดอิทธิพลของดอกเบี้ย เงินเฟ้อ และทุกปัจจัยตลาดเรียบร้อยแล้ว

<span id="network-stability"></span>

## เส้นอยู่ซ้ำแค่ไหนเมื่อเปลี่ยนช่วงฝึก

เราจะ fit ในช่วงย่อยยาว 104 สัปดาห์ โดยเลื่อนจุดเริ่มครั้งละ 13 สัปดาห์ภายใน training เดิม ได้เก้าช่วง แล้วนับว่าแต่ละเส้นปรากฏกี่ครั้งโดยคง alpha ที่เลือกไว้ การทำเช่นนี้เป็นการตรวจ sensitivity ของกราฟต่อช่วงข้อมูล

```python
subwindow_masks = []
for start in range(0, 105, 13):
    sample = train.iloc[start:start + 104].to_numpy()
    sample_z = (sample - sample.mean(axis=0)) / sample.std(axis=0, ddof=0)
    subwindow_masks.append(edge_mask(fit_graph(sample_z, chosen_alpha).precision_))
edge_frequency = np.mean(subwindow_masks, axis=0)
print('Number of overlapping windows:', len(subwindow_masks))
print(pd.DataFrame(edge_frequency, index=assets, columns=assets).round(2))
```

ตารางมีค่า 0 ถึง 1 เช่น 1 หมายถึงเส้นนั้นปรากฏครบเก้าช่วง ส่วน 0.44 หมายถึงประมาณสี่จากเก้าช่วง เราไม่ได้ใช้ test เข้ามานับ และไม่ได้ตีความตัวเลข 0.44 ว่าเป็นโอกาส 44% ที่ edge นั้นเป็นจริง

ช่วงย่อยเหล่านี้ทับซ้อนกันมากจึงไม่ใช่การทดลองอิสระ อีกทั้ง sample noise บางรูปอาจคงอยู่หลายช่วง ในตัวอย่าง A/E ปรากฏครบทุกช่วงย่อย ทั้งที่ precision ประชากรช่องนี้เป็นศูนย์ ความคงที่ของผลประมาณจึงไม่เท่ากับความถูกต้อง

บทคอร์สกล่าวถึง stability selection และการขยายไปยัง elliptical-copula graphical model เพื่อรองรับข้อมูลที่ต่างจาก Gaussian ตัวอย่างเก้าช่วงในหน้านี้เป็น sensitivity check แบบง่าย ไม่ได้ใช้ขั้นตอนหรือให้หลักประกันการควบคุม false discoveries ของวิธีวิจัยนั้น และไม่ได้ทำให้ Gaussian model กลายเป็นแบบจำลอง fat tails

<span id="network-mds-layout"></span>

## ตำแหน่งบนภาพเป็นการแสดงผลอีกขั้นหนึ่ง

สีของ node อาจมาจาก clustering ส่วนเส้นอาจมาจาก precision และตำแหน่งอาจมาจาก MDS ทั้งสามชั้นจึงไม่จำเป็นต้องใช้วัตถุประสงค์เดียวกัน การอยู่ใกล้กันในภาพไม่ได้บอกเองว่ามี edge หรือมี causal relationship

เราจะสร้างระยะจาก correlation ที่ประมาณได้ แล้วใช้ classical metric MDS หาพิกัดสองมิติ หาก $D^{(2)}$ เก็บระยะกำลังสองและ $J=I-\mathbf1\mathbf1^\top/n$ การทำ double centering ให้เมทริกซ์

$$B=-\frac12JD^{(2)}J.$$

$B$ เป็น Gram matrix ของพิกัดที่หักจุดศูนย์กลางแล้ว หา eigenvalues/eigenvectors ของ $B$ และเก็บสองแกนแรกเพื่อได้พิกัดสำหรับแสดงผล วิธีนี้ประมาณ Gram matrix ด้วยอันดับสอง ต่างจากการใช้ SMACOF ปรับตำแหน่งเพื่อหาค่า stress ต่ำ และต่างจาก nonmetric MDS ที่มุ่งรักษาลำดับของระยะ

```python
estimated_cov = graph_model.covariance_
estimated_corr = estimated_cov / np.sqrt(np.outer(np.diag(estimated_cov), np.diag(estimated_cov)))
graph_distance = np.sqrt(np.clip((1 - estimated_corr) / 2, 0, 1))
np.fill_diagonal(graph_distance, 0)
centering = np.eye(6) - np.ones((6, 6)) / 6
gram = -.5 * centering @ (graph_distance ** 2) @ centering
mds_values, mds_vectors = np.linalg.eigh(gram)
mds_order = np.argsort(mds_values)[::-1]
mds_values, mds_vectors = mds_values[mds_order], mds_vectors[:, mds_order]
for axis in range(2):
    pivot = np.argmax(np.abs(mds_vectors[:, axis]))
    if mds_vectors[pivot, axis] < 0:
        mds_vectors[:, axis] *= -1
network_coordinates = mds_vectors[:, :2] * np.sqrt(np.maximum(mds_values[:2], 0))
embedded_distance = squareform(pdist(network_coordinates))
upper = np.triu_indices(6, 1)
relative_distance_error = np.sqrt(np.sum((embedded_distance[upper] - graph_distance[upper]) ** 2)
                                  / np.sum(graph_distance[upper] ** 2))
print('2D relative distance error:', relative_distance_error)
print(pd.DataFrame(network_coordinates, index=assets, columns=['Display x', 'Display y']).round(4))
```

เราเลือกเครื่องหมายของแต่ละแกนให้สมาชิกที่มีขนาด loading สูงสุดเป็นบวก เพื่อให้ตารางแสดงทิศทางซ้ำได้ การกลับเครื่องหมายทั้งแกนเป็นเพียงการสะท้อนภาพ ไม่เปลี่ยนระยะระหว่างจุด และไม่ได้เพิ่มความหมายทางเศรษฐกิจให้แกน

`network_coordinates` มีหกแถวกับสองคอลัมน์ การหมุนหรือสะท้อนภาพทั้งภาพไม่เปลี่ยนระยะจึงไม่เปลี่ยนความหมาย แกน x/y ไม่มีหน่วยเป็นผลตอบแทนหรือความเสี่ยง และไม่มีความหมายว่าอยู่ขวาแล้วน่าลงทุนกว่า

เราเทียบระยะที่วัดจากภาพกับระยะต้นฉบับทุกคู่ ได้ relative distance error ประมาณ 0.30173 โดยใช้รากของผลรวม squared errors หารผลรวม squared original distances ค่านี้เป็นนิยามตรวจความคลาดเคลื่อนที่ระบุเอง ไม่ใช่ `stress_` จาก estimator ตัวอื่น ภาพสองมิติจึงยุบความแตกต่างบางคู่ไปมาก การรายงานเพียงภาพสวยโดยไม่บอกว่าระยะเพี้ยนได้จะทำให้ตีความเกินข้อมูล

<span id="network-asset-selection"></span>

## การเลือกหุ้นต้องเขียนกฎเพิ่มจากกราฟ

เราจะให้ Affinity Propagation จัดกลุ่มจาก estimated correlation distance ใช้ preference −0.4 ที่กำหนดก่อนเปิด test แล้วเลือกตัวแทนจากสมาชิกของแต่ละกลุ่มด้วยกฎคะแนนเสมอที่กำหนดไว้ ลงเงินเท่ากันในตัวแทนที่เลือก กฎนี้แสดงวิธีต่อ covariance estimation เข้ากับ clustering แต่ไม่ใช่การทำซ้ำวิธีเลือก isolated nodes ในงานวิจัยที่คอร์สอ้างถึง

ใช้ฟังก์ชัน `canonical_exemplars` แบบเดียวกับ [บทจัดกลุ่มสินทรัพย์](asset-clustering.html#affinity-propagation) โดยใส่โค้ดครบเพื่อให้ Notebook นี้รันแยกได้ หลัง AP กำหนดสมาชิกกลุ่มแล้ว เรารวม similarity เดิมจากสมาชิกทุกตัวถึงผู้สมัครแต่ละตัว เลือกคะแนนสูงที่สุด และเมื่อคะแนนต่างจากค่าสูงสุดไม่เกิน $10^{-12}$ ให้เลือกดัชนีน้อยที่สุด การเลือกนี้ใช้เฉพาะข้อมูลฝึก ไม่ใช้ผลตอบแทน test ตัดสินระหว่างผู้สมัคร

```python
def canonical_exemplars(similarity, labels, tolerance=1e-12):
    s = np.asarray(similarity, dtype=float)
    labels = np.asarray(labels)
    if labels.ndim != 1 or labels.size == 0 or s.shape != (labels.size, labels.size):
        raise ValueError('Provide one label per row of a square similarity matrix')
    if not np.isfinite(s).all() or not np.allclose(s, s.T, atol=1e-12, rtol=0):
        raise ValueError('Similarity must be finite and symmetric')
    if not np.issubdtype(labels.dtype, np.integer) or np.any(labels < 0):
        raise ValueError('Labels must be nonnegative integers')
    if not np.isfinite(tolerance) or tolerance < 0:
        raise ValueError('Tolerance must be finite and nonnegative')
    representatives = []
    for group in np.unique(labels):
        members = np.flatnonzero(labels == group)
        scores = s[np.ix_(members, members)].sum(axis=0)
        tied = members[scores >= scores.max() - tolerance]
        representatives.append(int(tied[0]))
    return np.sort(np.array(representatives, dtype=int))

graph_similarity = -(graph_distance ** 2)
with warnings.catch_warnings():
    warnings.simplefilter('error', ConvergenceWarning)
    graph_clusters = AffinityPropagation(affinity='precomputed', preference=-.4,
                                        damping=.8, max_iter=1000, random_state=7).fit(graph_similarity)
selected = canonical_exemplars(graph_similarity, graph_clusters.labels_)
selected_weights = np.zeros(6)
selected_weights[selected] = 1 / len(selected)
all_weights = np.full(6, 1 / 6)
print('Refined cluster exemplars:', assets[selected])
print('Network degrees:', adjacency.sum(axis=1))
print('Weights:', selected_weights)
```

ได้สมาชิกกลุ่ม AB/CD/EF แล้วกฎนี้เลือก A/C/E และน้ำหนักแต่ละตัว $1/3$ คู่ที่มีสองสมาชิกมีผลรวม similarity เท่ากันทางคณิตศาสตร์ เพราะเมทริกซ์สมมาตรและแนวทแยงเป็นศูนย์ จึงใช้ดัชนีแก้เสมอ การใช้ scalar preference เดียวกันแทนแนวทแยงก็เพิ่มคะแนนเท่ากันให้ผู้สมัครทุกตัวภายในกลุ่มเดิม

ตัวแทนที่พิมพ์และใช้ลงทุนเป็นผลของกฎหลังจัดกลุ่มนี้ ไม่ใช่ค่า `cluster_centers_indices_` ดิบ เราไม่ปัด similarity ไม่แก้ `graph_clusters.labels_` และไม่เลือกตัวแทนจากผลตอบแทนช่วงท้าย การสลับชื่อป้ายกลุ่มไม่เปลี่ยนรายชื่อที่ฟังก์ชันคืนมา แต่หากสมาชิกกลุ่มเปลี่ยน ผลเลือกก็อาจเปลี่ยนได้

ส่วน graph degree เป็นจำนวน edge ที่เชื่อม node นั้น ซึ่งในชุดนี้เท่ากับ 2, 5, 3, 4, 4, 4 ตามลำดับ A–F จำนวนเส้นต่ำอาจช่วยตั้งคำถามว่ารูปแบบการเคลื่อนไหวต่างจากตัวอื่นหรือไม่ แต่ยังไม่ได้รวมขนาด SD สภาพคล่อง ความเสี่ยงหาง หรือผลตอบแทนคาดหมาย

การคัดหุ้นตาม momentum หรือ value ก่อนสร้าง graph เป็นการเลือก universe อีกขั้นหนึ่ง ต้องใช้ signals และสมาชิก universe ที่รู้ได้ในวันนั้น และแยกผลของการคัดตาม factor ออกจากผลของการกระจายพอร์ต การเปรียบเทียบกับพอร์ตที่ใช้ universe หรือรอบ rebalancing คนละแบบจะยังแยกไม่ได้ว่าความต่างเกิดจากกราฟเพียงอย่างเดียว

งานของ Liu, Mulvey และ Zhao ศึกษา elliptical-copula model และการเลือกสินทรัพย์ร่วมกับ rebalancing เงื่อนไขและวิธีประเมินต่างจาก Gaussian example นี้ หน้านี้จึงไม่ยกตัวเลขผลตอบแทนของงานนั้นมารับรองผลของโค้ดเรา [A semiparametric graphical modelling approach for large-scale equity selection](https://pmc.ncbi.nlm.nih.gov/articles/PMC5354361/)

<span id="network-heldout-results"></span>

## วัดผลช่วงท้ายด้วยสมมติฐานเดียวกัน

เปรียบเทียบพอร์ตครบหกตัวกับพอร์ตตัวแทนหลังใช้กฎแก้เสมอ (`Refined exemplars`) ใน test 52 สัปดาห์ ทั้งคู่ปรับสู่น้ำหนักเป้าหมายทุกต้นสัปดาห์ ไม่มีต้นทุน ไม่มี leverage และใช้ผลตอบแทนชุดเดียวกัน การทบต้นเริ่มจากเงิน 1 ก่อนสัปดาห์ 209 โดยไม่บังคับขายปิดสถานะตอนสิ้นช่วง

```python
heldout_returns = pd.DataFrame({
    'All 6': test.to_numpy() @ all_weights,
    'Refined exemplars': test.to_numpy() @ selected_weights
}, index=test.index)
heldout_wealth = pd.concat([
    pd.DataFrame(1., index=[208], columns=heldout_returns.columns),
    (1 + heldout_returns).cumprod()
])
heldout_summary = pd.DataFrame({
    '52-week return': heldout_wealth.iloc[-1] - 1,
    'Annualized SD': heldout_returns.std(ddof=1) * np.sqrt(52),
    'Max drawdown': (heldout_wealth / heldout_wealth.cummax() - 1).min()
})
print(heldout_summary.round(5))
```

พอร์ตครบหกตัวให้ผลตอบแทนประมาณ 24.306% มี SD annualized 10.470% และ max drawdown −5.621% พอร์ตตัวแทน A/C/E ให้ผลตอบแทนประมาณ 22.117% มี SD 10.524% และ max drawdown −4.377% เส้นทางนี้จึงได้ผลตอบแทนต่ำกว่าและ SD สูงกว่าเล็กน้อย แต่ drawdown ตื้นกว่า การเลือกหนึ่งตัวต่อกลุ่มไม่ได้ทำให้ผลดีขึ้นพร้อมกันทุกมาตรวัด

ทั้งสองพอร์ตสมมติซื้อขายฟรี หากจะประเมินการลงทุนต้องเพิ่ม turnover, ต้นทุน และข้อจำกัดการซื้อขาย ดูขั้นตอนบัญชีเงินที่ [บท Diversification backtest](diversification-backtest.html) ตัวอย่างนี้มี test เพียงหนึ่งปีจำลองและความสัมพันธ์คงที่ ผลจึงไม่ตอบว่ารายชื่อจะยังเหมาะเมื่อ correlation หรือ regime เปลี่ยน

<span id="network-future-check"></span>

## เปลี่ยนอนาคตแล้วโมเดลจากอดีตต้องเท่าเดิม

```python
changed_returns = returns.copy()
changed_returns.iloc[208:, :] += .20
same_train = changed_returns.iloc[:208].to_numpy()
same_z = (same_train - same_train.mean(axis=0)) / same_train.std(axis=0, ddof=0)
repeat_model = fit_graph(same_z, chosen_alpha)
print('Graph unchanged after future mutation:', np.allclose(repeat_model.precision_, precision))
assert np.allclose(repeat_model.precision_, precision)
assert all(cutoff < end <= len(train) for cutoff, end in folds)
assert np.allclose(heldout_wealth.iloc[0], 1.)
```

โค้ดเพิ่มผลตอบแทนในสัปดาห์ 209–260 ทุกสินทรัพย์ 20 จุดเปอร์เซ็นต์ แต่ fit เฉพาะสัปดาห์ 1–208 อีกครั้ง กราฟจึงยังเท่าเดิม และตรวจว่า validation folds ไม่เกินขอบเขต training รวมถึงมีเงินต้น 1 อยู่ก่อนผลตอบแทนงวดแรก

การตรวจนี้ยืนยันเฉพาะเส้นแบ่งเวลาของตัวอย่าง หากทดลองหลาย universe, หลาย preference หรือหลายกฎเลือกหุ้นแล้วเก็บเฉพาะคำตอบที่ชนะบน test ก็ยังเกิดการเลือกผลเข้าข้างได้ ควรบันทึกทางเลือกก่อนดูช่วงทดสอบ และแยกการสำรวจข้อมูลออกจากการรายงานผลยืนยัน

<span id="network-exercises"></span>

## แบบฝึกหัดพร้อมเฉลย

1. ถ้า $K_{ii}=4$, $K_{jj}=9$, $K_{ij}=-1.2$ ค่า partial correlation เป็นเท่าไร

<details><summary>เฉลยข้อ 1</summary>

เท่ากับ $-(-1.2)/\sqrt{4\times9}=0.2$ ต้องกลับเครื่องหมายและหารด้วย 6 การรายงาน −1.2 เป็น correlation จะผิดทั้งเครื่องหมายและช่วงค่า

</details>

2. ในตัวอย่าง Z/X/Y ค่า correlation X/Y เป็น 0.48 แต่ partial correlation เป็นศูนย์ อธิบายได้อย่างไร

<details><summary>เฉลยข้อ 2</summary>

X/Y รับส่วนร่วมจาก Z ทำให้ covariance เป็น $0.8\times0.6$ หลังควบคุม Z เหลือ noise สองตัวที่เป็นอิสระกันตามสมมติฐาน การเป็นศูนย์จึงไม่ขัดกับการมี marginal correlation บวก

</details>

3. ตั้ง alpha สูงจนทุก edge หาย แปลว่าค้นพบหุ้นที่เป็นอิสระกันทั้งหมดหรือไม่

<details><summary>เฉลยข้อ 3</summary>

เป็นผลของ penalty ที่บังคับ estimated precision ให้บางมากขึ้น ตัวอย่างนี้เรารู้ว่าประชากรมีห้าเส้น แต่ alpha 0.60 ลบเส้นประมาณหมด จึงต้องแยกสมบัติของ estimator ออกจากสมบัติของข้อมูลจริง

</details>

4. Fit scaler จาก training 208 สัปดาห์ทั้งหมดแล้วใช้ใน fold ที่ฝึกเพียงสัปดาห์ 1–104 มีปัญหาอะไร

<details><summary>เฉลยข้อ 4</summary>

สเกลและ mean ใช้ข้อมูลจากสัปดาห์ 105–208 ซึ่งอยู่หลังจุดฝึกของ fold แรกไปแล้ว ควร fit preprocessing ภายในแต่ละ fold แล้วใช้ค่าชุดนั้น transform validation

</details>

5. เส้น A/E พบครบเก้าช่วงย่อย จึงมีโอกาสเป็นความสัมพันธ์จริง 100% ได้หรือไม่

<details><summary>เฉลยข้อ 5</summary>

ค่า 1 เป็นความถี่ที่ estimator ให้เส้นในเก้าช่วงที่ทับซ้อนกัน ไม่มีการแปลงเป็นความน่าจะเป็นว่าข้อสมมติเป็นจริง ในตัวอย่างนี้ true precision ช่อง A/E เป็นศูนย์อยู่แล้ว จึงเห็นว่าความถี่สูงไม่ได้ป้องกัน false edge

</details>

6. ถ้าหมุนพิกัด MDS ทั้งภาพ 90 องศา หรือเปลี่ยน layout ของภาพใหม่ ควรเปลี่ยนผลการเลือกหุ้นจาก precision หรือไม่

<details><summary>เฉลยข้อ 6</summary>

การหมุนคงระยะทุกคู่และไม่เปลี่ยน precision จึงไม่ควรเปลี่ยนการเลือกที่อาศัย precision ถ้ากฎเลือกขึ้นกับว่าจุดอยู่มุมขวาบนของภาพ กฎนั้นอาศัย orientation ของการแสดงผลที่ไม่มีความหมายทางการลงทุน

</details>

<span id="network-sources"></span>

## แหล่งที่มาและขอบเขตการอ่าน

อ่าน transcript เต็มของ Graphical analysis, Selecting a portfolio of assets และ Lab Graphical Network Analysis เมื่อ 3 ตุลาคม 2026 Lab อธิบายการเตรียม returns ของ 22 บริษัทจากสี่กลุ่มธุรกิจ ตามด้วย GraphicalLassoCV, Affinity Propagation และ MDS ไม่ได้รันหรือแจกไฟล์ Python, Notebook หรือข้อมูล CRSP ของผู้สอน โค้ดในบทนี้เป็น Gaussian simulation ที่เขียนใหม่ และใช้ chronological validation พร้อม scaler แยกแต่ละ fold

เปิดหน้า [รายการอ้างอิงการกระจายพอร์ต](https://www.coursera.org/learn/python-machine-learning-for-investment-management/supplement/jKOWy/references-for-the-module-machine-learning-techniques-for-efficient-portfolio) ซึ่งระบุ The Elements of Statistical Learning และหน้า [เอกสารประกอบการเลือกสินทรัพย์](https://www.coursera.org/learn/python-machine-learning-for-investment-management/supplement/L0ZQs/reference-for-the-module-selecting-a-portfolio-of-assets) ซึ่งเชื่อมบทความ semiparametric กับไฟล์ StabilitySelection อ่านข้อมูลบทความและข้อความส่วนที่เข้าถึงได้ผ่านดัชนีสาธารณะ แต่ไม่ได้อ่าน PDF แนบทั้งสองฉบับครบ จึงไม่อ้างว่า sensitivity check นี้ทำซ้ำอัลกอริทึมในเอกสาร

รายละเอียด objective และ normalization ตรวจจาก [เอกสาร covariance ของ scikit-learn](https://scikit-learn.org/stable/modules/covariance.html) และ [GraphicalLasso API](https://scikit-learn.org/stable/modules/generated/sklearn.covariance.GraphicalLasso.html) ส่วนการแยก metric/nonmetric MDS ตรวจจาก [เอกสาร MDS](https://scikit-learn.org/stable/modules/generated/sklearn.manifold.MDS.html) พิกัดในบทใช้ classical MDS ที่คำนวณด้วย NumPy เพื่อแสดงการลดมิติอย่างตรวจซ้ำได้ ไม่ได้เรียก estimator MDS ด้วยค่าปริยายที่เปลี่ยนตามรุ่น
