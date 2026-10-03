---
title: "PCA: พอร์ตมีความเสี่ยงกี่แหล่ง"
description: เริ่มจากจำนวนหุ้นและจำนวนความเสี่ยง คำนวณ eigenvectors, scores และ explained variance แล้วแยกสัดส่วนความแปรปรวนของข้อมูลออกจากความเสี่ยงของพอร์ต
---

# PCA: พอร์ตมีความเสี่ยงกี่แหล่ง

<p class="lead">ถือหุ้นหกตัวเท่ากันอาจยังรับความเสี่ยงหลักเพียงสองทิศทาง PCA ช่วยแยกทิศทางการเคลื่อนไหวร่วมของผลตอบแทน แล้วเราจึงตรวจได้ว่าพอร์ตให้น้ำหนักกับทิศทางไหนมาก</p>

สมมติหุ้น A กับ B มีรายได้จากลูกค้ากลุ่มเดียวกัน เมื่อความต้องการของลูกค้าลดลง หุ้นทั้งคู่ตกพร้อมกัน การแบ่งเงินระหว่างชื่อหุ้นสองชื่อจึงไม่ได้แบ่งความเสี่ยงทางเศรษฐกิจออกเป็นสองส่วนเท่ากันเสมอไป บท [วิธีจัดพอร์ตเพื่อกระจายความเสี่ยง](diversification-methods.html) วัดการกระจุกตัวจากน้ำหนักเงิน และบท [Risk contribution](risk-contributions.html) แบ่งความเสี่ยงกลับไปยังสินทรัพย์แต่ละตัว บทนี้จะเปลี่ยนฐานการมองจากชื่อสินทรัพย์เป็นทิศทางร่วมของข้อมูล

Principal Component Analysis หรือ PCA เป็นวิธีแปลงตัวแปรหลายตัวให้เป็นชุดตัวแปรใหม่ที่ไม่สัมพันธ์เชิงเส้นกันในข้อมูลที่ใช้ประมาณ ทิศทางแรกอธิบายความแปรปรวนได้มากที่สุด ทิศทางถัดไปอธิบายส่วนที่เหลือภายใต้เงื่อนไขว่าต้องตั้งฉากกับทิศทางก่อนหน้า เราจะคำนวณวิธีนี้จากตัวอย่างสองสินทรัพย์ ก่อนขยายเป็นข้อมูลสมมติหกสินทรัพย์

โค้ดทั้งบทใช้ NumPy, pandas และ scikit-learn รันจากต้นบทใน Notebook ใหม่ได้ ไม่มีราคาหุ้นจริงหรือไฟล์ข้อมูลจากคอร์ส ตัวอย่างสุ่มใช้ seed 317 เพื่อให้ทำซ้ำได้ ทุกแถวเป็นผลตอบแทนรายสัปดาห์หน่วยทศนิยม เช่น 0.02 หมายถึง 2% เนื้อหาเรียบเรียงใหม่ตามหัวข้อ [Benefits of portfolio diversification](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/16faT/benefits-of-portfolio-diversification), [Portfolio diversification measures](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/MWFae/portfolio-diversification-measures) และ [PCA](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/XsYTH/principle-component-analysis)

<span id="names-and-risk"></span>

## เริ่มจากชื่อหุ้นสองชื่อ

ถ้า A และ B มี SD ปีละ 20% และ correlation เท่ากับ 0.8 พอร์ตที่ลงคนละครึ่งมี covariance matrix และน้ำหนักดังนี้

$$
\Sigma=\begin{pmatrix}0.04&0.032\\0.032&0.04\end{pmatrix},
\qquad w=\begin{pmatrix}0.5\\0.5\end{pmatrix}.
$$

ช่อง 0.032 มาจาก $0.8\times0.2\times0.2$ ความแปรปรวนของพอร์ตเท่ากับ $0.5^2(0.04)+0.5^2(0.04)+2(0.5)(0.5)(0.032)=0.036$ จึงมี SD $\sqrt{0.036}\approx18.9737\%$ ต่อปี ต่ำกว่า SD 20% ของแต่ละตัว แต่ไม่ได้ลดเหลือครึ่งหนึ่ง

จำนวนสินทรัพย์ตามการกระจุกตัวของเงิน หรือ [effective number of assets](glossary.html#effective-number-assets) เท่ากับ

$$N_{\text{capital}}=\frac{1}{\sum_iw_i^2}=\frac{1}{0.5^2+0.5^2}=2.$$

```python
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

small_cov = np.array([[0.04, 0.032], [0.032, 0.04]])
small_w = np.array([0.5, 0.5])
small_enc = 1 / np.sum(small_w ** 2)
small_variance = small_w @ small_cov @ small_w
print('ENC:', small_enc)
print('Portfolio SD:', np.sqrt(small_variance))
print('Covariance eigenvalues:', np.linalg.eigvalsh(small_cov)[::-1])
```

ตัวเลข `2.0` บอกว่าลงเงินเท่ากันสองส่วน ส่วน `0.189736...` คือ SD ของพอร์ต ไม่ใช่ผลตอบแทนคาดหมาย บรรทัดสุดท้ายได้ eigenvalues 0.072 และ 0.008 ซึ่งเป็นความแปรปรวนตามทิศทางใหม่สองทิศทางที่กำลังจะคำนวณ

เราหาทิศทางเหล่านั้นได้ด้วยมือ

$$v_1=\frac{1}{\sqrt2}(1,1)^\top,\qquad
v_2=\frac{1}{\sqrt2}(1,-1)^\top.$$

ทิศทางแรกจับการขึ้นลงร่วมกัน ส่วนทิศทางที่สองจับส่วนต่าง A กับ B เมื่อคูณ $\Sigma v_1$ จะได้ $0.072v_1$ และเมื่อคูณ $\Sigma v_2$ จะได้ $0.008v_2$ จึงเรียก $v_k$ ว่า eigenvector และตัวคูณ $\lambda_k$ ว่า eigenvalue

PCA จัดความแปรปรวนของข้อมูลให้ทิศทางแรก $0.072/(0.072+0.008)=90\%$ ส่วนที่สอง 10% แต่พอร์ตครึ่งต่อครึ่งมี $v_2^\top w=0$ จึงไม่รับความเสี่ยงจากทิศทางส่วนต่างเลย ความเสี่ยงของพอร์ตนี้มาจาก PC1 ทั้งหมด แม้ PC1 จะอธิบายความแปรปรวนของข้อมูลเพียง 90%

<span id="pca-teaching-data"></span>

## สร้างข้อมูลที่ตรวจที่มาได้

ต่อไปใช้ A–F จำนวน 260 สัปดาห์ แบ่ง 208 สัปดาห์แรกไว้เรียนรู้โครงสร้าง และเก็บ 52 สัปดาห์ท้ายไว้ตรวจภายหลัง สินทรัพย์แต่ละตัวมีค่าเฉลี่ยตามแบบจำลอง 0.1% ต่อสัปดาห์ และ SD ที่กำหนดต่างกัน การสุ่มหนึ่งชุดย่อมมีค่าเฉลี่ยกับ covariance ของตัวอย่างคลาดจากค่าที่กำหนด

โค้ดตั้งต้นด้วยเมทริกซ์ `true_precision` แล้วกลับเมทริกซ์เพื่อสร้าง covariance พื้นฐาน วิธีสร้างนี้ทำให้รู้ความสัมพันธ์ที่แท้จริงของแบบจำลองไว้ตรวจใน [บทเครือข่ายสินทรัพย์](asset-networks.html) ตอนนี้ใช้เพียงผลลัพธ์ `true_cov` ซึ่งเป็น covariance รายสัปดาห์ ทุกสัปดาห์สุ่มอย่างเป็นอิสระจากการแจกแจงร่วม Normal ที่มีพารามิเตอร์คงที่ จึงยังไม่มี volatility clustering หรือการเปลี่ยน regime

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

`np.eye(6)` สร้างเมทริกซ์เอกลักษณ์ขนาด $6\times6$ `np.outer` คูณ SD ทุกคู่ และ `np.linalg.cholesky(true_cov)` ให้เมทริกซ์ $L$ ที่ $LL^\top=\Sigma$ ถ้าแถวสุ่ม $u$ มี covariance เป็นเมทริกซ์เอกลักษณ์ แถว `u @ L.T` จะมี covariance ตามที่ต้องการ เครื่องหมาย `.T` สลับแถวกับคอลัมน์

`iloc[:208]` เลือกตำแหน่งแถว 0 ถึง 207 ซึ่งติดป้ายสัปดาห์ 1 ถึง 208 ส่วน `iloc[208:]` เริ่มที่สัปดาห์ 209 การพิมพ์ shape ได้ `(208, 6)` กับ `(52, 6)` จึงตรวจได้ว่าแถวคือเวลา คอลัมน์คือสินทรัพย์ ตัวอย่าง Normal ของ simple returns มีโอกาสเชิงทฤษฎีที่จะต่ำกว่า −100%; ข้อมูลที่สุ่มได้ครั้งนี้ไม่มีค่าดังกล่าว แบบจำลองนี้ใช้สอน covariance และไม่ได้เป็นแบบจำลองราคาหุ้นที่รับรองราคาบวกทุกเส้นทาง

<span id="pca-eigenvectors"></span>

## หักค่าเฉลี่ยก่อนหาทิศทาง

ให้ $R$ เป็นตารางผลตอบแทน 208 แถว 6 คอลัมน์ หักค่าเฉลี่ยของแต่ละคอลัมน์ออกจะได้ $X$ แล้วคำนวณ sample covariance

$$S=\frac{X^\top X}{T-1},\qquad T=208.$$

PCA บน covariance แก้สมการ $Sv_k=\lambda_kv_k$ สำหรับทุกทิศทาง เมื่อเรียง eigenvalues จากมากไปน้อยและรวม eigenvectors เป็นคอลัมน์ของ $V$ จะเขียนได้ว่า

$$S=V\Lambda V^\top,\qquad V^\top V=I.$$

$\Lambda$ เป็นเมทริกซ์แนวทแยงที่เก็บ $\lambda_1,\ldots,\lambda_6$ ส่วน $I$ คือเมทริกซ์เอกลักษณ์ เงื่อนไข $V^\top V=I$ บอกว่าทุกเวกเตอร์ยาวหนึ่งและตั้งฉากกัน เวกเตอร์เหล่านี้เป็นสัมประสิทธิ์สำหรับผสมผลตอบแทนของ A–F ไม่ใช่ชื่อหุ้นที่ PCA เลือกให้ซื้อ

```python
train_mean = train.mean().to_numpy()
centered = train.to_numpy() - train_mean
sample_cov = centered.T @ centered / (len(train) - 1)
eigenvalues, eigenvectors = np.linalg.eigh(sample_cov)
order = np.argsort(eigenvalues)[::-1]
eigenvalues = eigenvalues[order]
eigenvectors = eigenvectors[:, order]
# Choose a consistent sign for display; the direction is unchanged.
for k in range(len(assets)):
    pivot = np.argmax(np.abs(eigenvectors[:, k]))
    if eigenvectors[pivot, k] < 0:
        eigenvectors[:, k] *= -1
print('Eigenvalues:', np.round(eigenvalues, 8))
print('Orthonormal:', np.allclose(eigenvectors.T @ eigenvectors, np.eye(6)))
```

`np.linalg.eigh` ใช้กับเมทริกซ์สมมาตรและคืนค่าจากน้อยไปมาก เราจึงเรียงใหม่ด้วย `argsort(...)[::-1]` ค่า eigenvalues ที่ได้ประมาณ 0.00157115, 0.00105106, 0.00067960, 0.00049221, 0.00027268 และ 0.00019914 หน่วยคือผลตอบแทนทศนิยมยกกำลังสองต่อสัปดาห์ ผลตรวจ `Orthonormal` ต้องเป็น `True`

เครื่องหมายของ eigenvector กลับด้านได้ เช่น $(1,1)/\sqrt2$ กับ $(-1,-1)/\sqrt2$ บรรยายเส้นเดียวกัน โค้ดเลือกให้สัมประสิทธิ์ที่มีขนาดสัมบูรณ์มากที่สุดเป็นบวกเพื่อให้อ่านตารางซ้ำได้ การกลับเครื่องหมายนี้ไม่เปลี่ยน eigenvalue หรือความเสี่ยงที่คำนวณจากทิศทางนั้น

<span id="pca-scores"></span>

## Scores คือผลตอบแทนในพิกัดใหม่

สัมประสิทธิ์ $v_k$ เป็นกฎสำหรับผสมสินทรัพย์ ส่วน score คือค่าที่ได้ในแต่ละสัปดาห์

$$F=XV,\qquad F_{tk}=\sum_iX_{ti}v_{ik}.$$

ตาราง $F$ ยังมี 208 แถว แต่คอลัมน์เปลี่ยนจาก A–F เป็น PC1–PC6 เช่น score ของ PC1 ในสัปดาห์แรกได้จากผลรวมของผลตอบแทนที่หักค่าเฉลี่ยแล้วทั้งหกตัว คูณสัมประสิทธิ์ PC1 ของแต่ละตัว

เมื่อใช้ครบทุกองค์ประกอบ เรากลับไปหาข้อมูลเดิมได้ด้วย $X=FV^\top$ เพราะการหมุนแกนยังไม่ได้ทิ้งข้อมูล การลดมิติจะเกิดขึ้นเมื่อเก็บไว้เพียงบางคอลัมน์ของ $F$

```python
scores = centered @ eigenvectors
score_cov = np.cov(scores, rowvar=False, ddof=1)
reconstruction = scores @ eigenvectors.T + train_mean
print('Score covariance diagonal:', np.round(np.diag(score_cov), 8))
print('Largest reconstruction error:', np.max(np.abs(reconstruction - train)))
assert np.allclose(score_cov, np.diag(eigenvalues), atol=1e-12)
assert np.allclose(reconstruction, train)
```

`np.cov(..., rowvar=False)` กำหนดว่าตัวแปรอยู่ตามคอลัมน์ ค่าแนวทแยงของ covariance ของ scores ตรงกับ eigenvalues ส่วนค่าข้ามคอลัมน์ใกล้ศูนย์ ความคลาดเคลื่อนจากการสร้างข้อมูลกลับประมาณ $7.6\times10^{-17}$ เป็นระดับความละเอียดของเลขทศนิยมในเครื่อง

Scores จึงไม่สัมพันธ์เชิงเส้นกันในข้อมูลฝึก ภายใต้แบบจำลองร่วม Gaussian ที่กำหนดไว้ เราตีความองค์ประกอบประชากรที่ไม่สัมพันธ์กันว่าเป็นอิสระกันได้ แต่ข้อมูลตลาดทั่วไปอาจสัมพันธ์กันในรูปอื่นที่ covariance มองไม่เห็น และ scores ในข้อมูลอนาคตไม่จำเป็นต้องมี sample covariance เป็นแนวทแยง

<span id="pca-explained-variance"></span>

## Explained variance วัดสิ่งที่เหลือหลังลดมิติ

สัดส่วนความแปรปรวนของข้อมูลที่ PC ตัวที่ $k$ อธิบายได้คือ

$$e_k=\frac{\lambda_k}{\sum_j\lambda_j}.$$

ตัวหารคือผลรวม variance ของคอลัมน์เดิม ไม่ใช่ variance ของพอร์ตใดพอร์ตหนึ่ง ถ้าตั้งเกณฑ์ว่าจะเก็บอย่างน้อย 80% ให้บวก $e_k$ จาก PC1 ลงมา จนผลรวมถึงเกณฑ์ แล้วเก็บทิศทางเหล่านั้น

```python
explained_ratio = eigenvalues / eigenvalues.sum()
cumulative_ratio = np.cumsum(explained_ratio)
n_components_80 = int(np.searchsorted(cumulative_ratio, .80) + 1)
retained = eigenvectors[:, :n_components_80]
rank_reconstruction = centered @ retained @ retained.T
squared_error = np.sum((centered - rank_reconstruction) ** 2)
expected_error = (len(train) - 1) * eigenvalues[n_components_80:].sum()
print(pd.DataFrame({'PC': np.arange(1, 7), 'Data variance %': explained_ratio * 100,
                    'Cumulative %': cumulative_ratio * 100}).round(3))
print('Components reaching 80%:', n_components_80)
print('Reconstruction SSE:', squared_error)
assert np.isclose(squared_error, expected_error)
```

PC1 อธิบายได้ประมาณ 36.831% สองตัวแรกรวม 61.470% และสามตัวแรกรวม 77.401% จึงต้องเก็บสี่ตัวจึงถึงเกณฑ์ 80% โดยได้จริงประมาณ 88.940% ค่า 80% เป็นเกณฑ์ที่เลือกเพื่อทดลอง ไม่ใช่กฎว่าพอร์ตควรมีสี่สินทรัพย์

การสร้างกลับด้วยสี่แกนทำให้ผลรวม squared reconstruction errors ประมาณ 0.09766655 ค่านี้เท่ากับ $(T-1)$ คูณผลรวม eigenvalues ที่ทิ้งไป โค้ดตรวจความเท่ากันด้วย `np.isclose` ถ้าใช้ครบหกแกน error จะใกล้ศูนย์ แต่ไม่ได้แปลว่าโมเดลทำนายอนาคตได้ดีขึ้น เพราะการสร้างข้อมูลฝึกกลับกับการคาดการณ์เป็นคนละงาน

<span id="pca-portfolio-risk"></span>

## ความเสี่ยงของพอร์ตขึ้นกับน้ำหนักด้วย

พอร์ตมีน้ำหนัก $w$ จึงมี variance $w^\top Sw$ แทน $S=V\Lambda V^\top$ ลงไปจะได้

$$
\sigma_p^2=\sum_k\lambda_k(v_k^\top w)^2.
$$

ตัวเลข $b_k=v_k^\top w$ คือ exposure ของพอร์ตต่อแกนที่ $k$ ส่วน $c_k=\lambda_kb_k^2$ คือส่วนของ variance จากแกนนั้น ทุก $c_k$ ไม่ติดลบและรวมเป็น variance ของพอร์ต เมื่อ variance รวมเป็นบวก จึงนิยามส่วนแบ่ง $p_k=c_k/\sigma_p^2$ ได้

ในตัวอย่างสองหุ้นตอนต้น $b_1=1/\sqrt2$ และ $b_2=0$ ทำให้ $c_1=0.072/2=0.036$ และ $c_2=0$ คราวนี้คำนวณพอร์ต equal-weight (EW) ที่ลงเงินในหกสินทรัพย์ตัวละ $1/6$

```python
weights = np.full(6, 1 / 6)
exposures = eigenvectors.T @ weights
pc_variance = eigenvalues * exposures ** 2
portfolio_variance = weights @ sample_cov @ weights
risk_shares = pc_variance / portfolio_variance
inverse_hhi_bets = 1 / np.sum(risk_shares ** 2)
positive_shares = risk_shares[risk_shares > 0]
entropy_bets = np.exp(-np.sum(positive_shares * np.log(positive_shares)))
print(pd.DataFrame({'PC': np.arange(1, 7), 'Data variance %': explained_ratio * 100,
                    'Portfolio variance %': risk_shares * 100}).round(3))
print('ENC / inverse HHI / entropy:', 1 / np.sum(weights ** 2),
      inverse_hhi_bets, entropy_bets)
assert np.isclose(pc_variance.sum(), portfolio_variance)
```

แม้ PC1 อธิบายข้อมูลมากที่สุด แต่พอร์ตนี้มีส่วนแบ่งความเสี่ยงจาก PC2 มากกว่า: PC1 ประมาณ 40.440% และ PC2 ประมาณ 51.600% รวมสองแกนเป็นประมาณ 92.04% ของ variance พอร์ต ตัวเลขนี้ต่างจาก 61.470% ซึ่งเป็นสัดส่วนความแปรปรวนของข้อมูลที่สองแกนแรกอธิบายได้

<figure class="lesson-figure">
<picture>
<source media="(max-width: 520px)" srcset="assets/charts/ml-pca-risk-shares-mobile.svg">
<img src="assets/charts/ml-pca-risk-shares.svg" alt="ส่วนแบ่งความแปรปรวนของข้อมูลกับส่วนแบ่งความแปรปรวนพอร์ต EW ในหกแกน PCA จากข้อมูลจำลอง" loading="lazy" width="720" height="560">
</picture>
<figcaption>คำนวณจากข้อมูลจำลอง 208 สัปดาห์แรก seed 317 แท่งม่วงเป็น eigenvalue shares ส่วนแท่งเขียวคูณ exposure ของพอร์ต EW เข้ามาด้วย แต่ละสีรวมเป็น 100% โดยใช้ตัวหารต่างกัน</figcaption>
</figure>

เราย่อการกระจุกตัวของ $p$ ได้หลายสูตร โค้ดแสดงทั้ง $1/\sum_kp_k^2\approx2.308174$ และ $\exp(-\sum_{p_k>0}p_k\log p_k)\approx2.650338$ สูตรแรกเป็น inverse HHI ของส่วนแบ่งความเสี่ยง ส่วนสูตรที่สองเป็นจำนวนเชิง entropy ถ้าความเสี่ยงแบ่งเท่ากัน $m$ ส่วน ทั้งสองสูตรจะให้ $m$ แต่เมื่อส่วนแบ่งไม่เท่ากันค่าจะต่างกัน จึงต้องเขียนสูตรกำกับคำว่า effective number ทุกครั้ง

แนวคิด Effective Number of Bets ของ Meucci ใช้ entropy ของการแจกแจงส่วนแบ่งความเสี่ยง การรายงาน inverse HHI ในคอร์สเป็นอีก convention หนึ่ง อย่านำตัวเลขสองสูตรมาเทียบกันโดยไม่ตรวจนิยาม และทั้งสองค่ายังขึ้นกับฐาน factors ที่เลือก ไม่ได้รับรองว่าพอร์ตมีแหล่งรายได้ทางเศรษฐกิจที่เป็นอิสระจำนวนเท่านั้น [Meucci, Managing Diversification](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1358533)

<span id="covariance-or-correlation-pca"></span>

## ใช้ covariance หรือ correlation จะตอบต่างกัน

PCA บน covariance ให้สินทรัพย์ที่มี SD สูงมีอิทธิพลต่อทิศทางมากกว่า หากต้องการเริ่มจากทุกสินทรัพย์ในสเกล SD หนึ่งหน่วย ให้หักค่าเฉลี่ยแล้วหาร SD รายตัว

$$Z_{ti}=\frac{R_{ti}-\bar R_i}{s_i},\qquad
C=\frac{Z^\top Z}{T-1}.$$

$C$ คือ sample correlation matrix และมีแนวทแยงเป็นหนึ่ง การทำเช่นนี้ไม่ได้ลบความเสี่ยงจากสินทรัพย์จริงออกไป เพียงเปลี่ยนหน่วยที่ใช้ค้นหาทิศทาง ถ้าจะนำผลกลับมาวิเคราะห์พอร์ตเดิม ต้องคูณ SD กลับด้วย

ให้ $D=\operatorname{diag}(s_1,\ldots,s_6)$ จะได้ $S=DCD$ ถ้า $C=U\Lambda_CU^\top$ ความแปรปรวนพอร์ตจึงเป็น

$$w^\top Sw=\sum_k\lambda_{C,k}(u_k^\top Dw)^2.$$

```python
train_sd = train.std(ddof=1).to_numpy()
standardized = centered / train_sd
sample_corr = standardized.T @ standardized / (len(train) - 1)
corr_values, corr_vectors = np.linalg.eigh(sample_corr)
corr_values, corr_vectors = corr_values[::-1], corr_vectors[:, ::-1]
scaled_weights = train_sd * weights
corr_pc_variance = corr_values * (corr_vectors.T @ scaled_weights) ** 2
print('Correlation PCA data shares:', np.round(corr_values / corr_values.sum(), 4))
print('Same portfolio variance:', corr_pc_variance.sum(), portfolio_variance)
assert np.isclose(corr_pc_variance.sum(), portfolio_variance)
```

สัดส่วนความแปรปรวนของ correlation PCA ประมาณ 27.94%, 27.27%, 21.30%, 8.95%, 8.40%, 6.14% ต่างจาก covariance PCA ก่อนหน้า แต่เมื่อใช้ `scaled_weights = train_sd * weights` จะกลับมาได้ variance พอร์ตเดียวกันคือประมาณ 0.0001869832 ต่อสัปดาห์

ถ้าลืมคูณ SD กลับและใช้ `corr_vectors.T @ weights` จะได้ความเสี่ยงของพอร์ตในตัวแปรที่ปรับหน่วยแล้ว ผลนั้นไม่มีหน่วยตรงกับผลตอบแทนพอร์ตที่ลงทุนด้วยน้ำหนัก $w$ ใน A–F ส่วนการเลือก covariance หรือ correlation ควรเริ่มจากคำถามว่าต้องการรักษาขนาดความผันผวนไว้ในระยะห่างหรือไม่

<span id="pca-python-api"></span>

## ตรวจด้วย PCA ของ scikit-learn

เมื่อเข้าใจการคูณเมทริกซ์แล้ว เราใช้ `PCA` ทำงานเดียวกันได้ ตัว estimator หักค่าเฉลี่ยให้ แต่ไม่หาร SD ให้อัตโนมัติ และ `explained_variance_` ใช้ตัวหาร $T-1$ เราจะระบุ `svd_solver='full'` และ `whiten=False` ให้ชัดเจน การ whiten จะปรับสเกล scores เพิ่มเติม จึงไม่ใช่ scores หน่วยเดิมที่คำนวณไว้ข้างต้น [เอกสาร PCA](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html)

```python
pca = PCA(n_components=6, svd_solver='full', whiten=False).fit(train)
sklearn_scores = pca.transform(train)
print('Same eigenvalues:', np.allclose(pca.explained_variance_, eigenvalues))
print('Same explained ratios:', np.allclose(pca.explained_variance_ratio_, explained_ratio))
print('Reconstruct training data:', np.allclose(pca.inverse_transform(sklearn_scores), train))
assert np.allclose(pca.components_.T @ pca.components_, np.eye(6))
```

ผลสามบรรทัดเป็น `True` เครื่องหมายของ `pca.components_` อาจกลับด้านจาก `eigenvectors` ได้ จึงตรวจ eigenvalues, explained ratios และการสร้างกลับแทนการบังคับว่าเมทริกซ์สัมประสิทธิ์ต้องเหมือนกันทุกช่อง `components_` เก็บหนึ่งองค์ประกอบต่อแถว ต่างจาก `eigenvectors` ที่เก็บหนึ่งองค์ประกอบต่อคอลัมน์

<span id="pca-future-transform"></span>

## ใช้แกนที่เรียนจากอดีตกับสัปดาห์ถัดไป

หลังจบสัปดาห์ 208 เรามีค่าเฉลี่ยและแกน PCA ที่เรียนจากข้อมูล 208 แถวเท่านั้น เมื่อผลตอบแทนสัปดาห์ 209 มาถึง จึงหักค่าเฉลี่ยชุดเดิมแล้วคูณแกนเดิม การใช้ `transform` กับข้อมูลท้ายชุดทำเช่นนี้ให้ ส่วนการ `fit` ใหม่ด้วยทั้ง 260 แถวจะให้ข้อมูลอนาคตย้อนมามีส่วนกำหนดแกน

```python
heldout_scores = pca.transform(test)
future_changed = returns.copy()
future_changed.iloc[208:, 0] += .20
pca_again = PCA(n_components=6, svd_solver='full').fit(future_changed.iloc[:208])
print('Training components unchanged:', np.allclose(pca.components_, pca_again.components_))
print('Held-out scores shape:', heldout_scores.shape)
print('Held-out PC1 mean:', heldout_scores[:, 0].mean())
assert np.allclose(pca.components_, pca_again.components_)
```

ตาราง held-out scores มี shape `(52, 6)` ค่าเฉลี่ย PC1 ในชุดท้ายประมาณ 0.00703848 และไม่จำเป็นต้องเป็นศูนย์ เพราะใช้ค่าเฉลี่ยฝึกหักออก โค้ดเพิ่มผลตอบแทน A ในอนาคต 20 จุดเปอร์เซ็นต์ แล้ว fit เฉพาะอดีตซ้ำ ผล `Training components unchanged` ยังเป็น `True` จึงตรวจได้ว่าการเรียนแกนไม่อ่านแถวในอนาคต

หากจะเลือกจำนวน PC จากผลการลงทุน ต้องแยกช่วงสำหรับเลือกจำนวนนั้นไว้ในข้อมูลฝึกอีกชั้น ก่อนเปิดข้อมูลท้ายชุด เปลี่ยนจำนวน PC จนผล 52 สัปดาห์ท้ายดูดีกว่าเดิมแล้วเรียกช่วงนั้นว่า test จะทำให้คำว่า held-out หมดความหมาย

<span id="pca-limits"></span>

## สองข้อจำกัดที่เห็นจากตัวเลขสั้น ๆ

ตัวแปร $u$ กับ $u^2$ อาจมี correlation เป็นศูนย์ แต่เมื่อรู้ $u$ เราคำนวณ $u^2$ ได้ทันที จึงยังพึ่งพากัน อีกกรณีคือ covariance ที่มี eigenvalues เท่ากัน ซึ่งเลือกแกนตั้งฉากได้หลายชุด การแบ่งส่วนความเสี่ยงให้แต่ละแกนจึงเปลี่ยนตามฐานที่เลือก

```python
u = np.array([-2., -1., 0., 1., 2.])
v = u ** 2
print('Correlation(u, u squared):', np.corrcoef(u, v)[0, 1])
identity_cov = np.eye(2)
w_basis = np.array([1., 0.])
rotation = np.array([[1., 1.], [1., -1.]]) / np.sqrt(2)
shares_original = w_basis ** 2
shares_rotated = (rotation.T @ w_basis) ** 2
print('Identity-basis risk shares:', shares_original)
print('Rotated-basis risk shares:', shares_rotated)
assert np.allclose(rotation.T @ identity_cov @ rotation, np.eye(2))
```

ตัวอย่างแรกได้ correlation ศูนย์แม้ $v=u^2$ ทุกแถว ตัวอย่างที่สองใช้ covariance เป็น $I$ และพอร์ต $w=(1,0)$ ถ้าใช้แกนเดิม ส่วนแบ่งความเสี่ยงคือ $(1,0)$ แต่ถ้าหมุนแกน 45 องศา จะได้ $(0.5,0.5)$ ทั้งที่ covariance และ variance พอร์ตยังเท่าเดิม สูตร inverse HHI จึงเปลี่ยนจาก 1 เป็น 2 ตามฐานนี้

เมื่อ eigenvalues อยู่ใกล้กันมาก ข้อมูลที่เปลี่ยนเล็กน้อยอาจทำให้แกนแต่ละตัวหมุนมาก แม้พื้นที่ที่หลายแกนร่วมกันอธิบายจะเปลี่ยนน้อย การตั้งชื่อ PC1 ว่า “ตลาด” หรือ PC2 ว่า “พลังงาน” ต้องมีหลักฐานจาก loadings และตัวแปรภายนอก ไม่ใช่ตั้งชื่อจากลำดับเพียงอย่างเดียว

[Sparse PCA](https://scikit-learn.org/stable/modules/decomposition.html#sparse-principal-components-analysis-sparsepca-and-minibatchsparsepca) เพิ่มเงื่อนไขให้สัมประสิทธิ์บางตัวเป็นศูนย์เพื่ออ่านความเกี่ยวข้องของสินทรัพย์ได้ง่ายขึ้น แต่ไม่ได้รับเงื่อนไข orthogonality และการแบ่ง variance แบบ ordinary PCA มาทั้งหมด จึงไม่ควรนำ eigenvalue shares ข้างต้นไปใช้กับ Sparse PCA โดยไม่ตรวจวิธีนิยามใหม่ บทถัดไปจะ [จัดกลุ่มสินทรัพย์และเลือกตัวแทน](asset-clustering.html) ซึ่งเป็นอีกงานหนึ่งจากการหาแกนผสมผลตอบแทน

<span id="pca-exercises"></span>

## แบบฝึกหัดพร้อมเฉลย

1. ในตัวอย่างสองหุ้น covariance ช่องนอกแนวทแยงเปลี่ยนเป็นศูนย์ โดย SD ของแต่ละหุ้นยัง 20% พอร์ตครึ่งต่อครึ่งมี SD เท่าไร และ ENC เปลี่ยนหรือไม่

<details><summary>เฉลยข้อ 1</summary>

Variance เท่ากับ $0.25(0.04)+0.25(0.04)=0.02$ ทำให้ SD ประมาณ 14.1421% ต่อปี ENC ยังเท่ากับ 2 เพราะสูตรนับการกระจุกตัวของเงินไม่ได้ใช้ covariance

</details>

2. ถ้า eigenvalues เท่ากับ 5, 3, 2 ต้องเก็บกี่องค์ประกอบเพื่ออธิบายข้อมูลอย่างน้อย 80%

<details><summary>เฉลยข้อ 2</summary>

สององค์ประกอบแรกให้ $(5+3)/(5+3+2)=80\%$ พอดี เกณฑ์นี้ยังไม่ได้ใช้ $w$ จึงยังตอบไม่ได้ว่าสองแกนนั้นอธิบายความเสี่ยงของพอร์ตที่กำลังลงทุนเท่าไร

</details>

3. ถ้า eigenvalues เป็น 0.04 และ 0.01 และ exposure ของพอร์ตต่อสองแกนเป็น 0.2 กับ 0.8 ส่วนแบ่งความเสี่ยงคือเท่าไร

<details><summary>เฉลยข้อ 3</summary>

Variance contributions คือ $0.04(0.2)^2=0.0016$ และ $0.01(0.8)^2=0.0064$ รวม 0.008 จึงแบ่งเป็น 20% กับ 80% แม้ eigenvalue แรกมากกว่า แกนที่สองกลับสร้าง variance ให้พอร์ตมากกว่าเพราะ exposure มากกว่า

</details>

4. เปลี่ยน eigenvector เป็นค่าลบของมันแล้ว exposure และ variance contribution เปลี่ยนอย่างไร

<details><summary>เฉลยข้อ 4</summary>

Exposure กลับเครื่องหมาย แต่ $\lambda_kb_k^2$ เท่าเดิม Scores กลับเครื่องหมายด้วย ถ้าใช้เครื่องหมายสอดคล้องกันทั้งตอนแปลงและสร้างกลับ ข้อมูลที่สร้างกลับไม่เปลี่ยน

</details>

5. หลังทำ correlation PCA ต้องคูณเวกเตอร์น้ำหนักด้วยอะไรเพื่อคำนวณ variance ของพอร์ตผลตอบแทนเดิม

<details><summary>เฉลยข้อ 5</summary>

คูณด้วยเมทริกซ์ SD แนวทแยง $D$ ก่อนคำนวณ exposure เป็น $U^\top Dw$ เพราะผลตอบแทนที่หักค่าเฉลี่ยในหน่วยเดิมเท่ากับตัวแปรที่ standardized แล้วคูณ SD กลับ

</details>

6. พอร์ตมี risk shares $(0.8,0.2)$ จงคำนวณ effective count สองสูตร และอธิบายว่าทำไมไม่ควรใช้แทนจำนวนหุ้น

<details><summary>เฉลยข้อ 6</summary>

Inverse HHI เท่ากับ $1/(0.8^2+0.2^2)=1.470588$ ส่วน entropy count เท่ากับ $\exp[-0.8\log(0.8)-0.2\log(0.2)]\approx1.649385$ ทั้งสองวัดการกระจุกตัวของ risk shares ในฐานที่กำหนด ไม่ได้บอกจำนวนชื่อหุ้นที่ถือ และยังไม่ได้พิสูจน์ independence

</details>

<span id="pca-sources"></span>

## แหล่งที่มาและขอบเขตการอ่าน

ตรวจแหล่งที่มาเมื่อ 3 ตุลาคม 2026: อ่าน transcript เต็มของบทแนะนำส่วนการกระจายพอร์ต, Benefits of portfolio diversification, Portfolio diversification measures และ PCA ผ่านบัญชีที่เข้าถึงคอร์สได้ ตัวอย่าง สมการที่ทำด้วยมือ และ Python ในหน้านี้เขียนใหม่ทั้งหมด จึงไม่ใช่การทำซ้ำผลตลาดของผู้สอน

ใช้ Transcript และเอกสาร scikit-learn สำหรับรายละเอียด PCA โดยไม่ได้ใช้ PDF ประกอบเป็นแหล่งรายละเอียด แยกสูตร entropy จาก inverse HHI ตามแหล่ง Meucci ที่ลิงก์ไว้ข้างต้น โค้ดตรวจด้วย scikit-learn 1.6.1; เครื่องหมาย eigenvectors และทศนิยมท้ายอาจต่างตามรุ่นของไลบรารี
