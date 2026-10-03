---
title: "จัดกลุ่มสินทรัพย์และเลือกตัวแทน"
description: แปลง correlation เป็นระยะห่าง เปรียบเทียบ medoids, k-means, hierarchical clustering และ affinity propagation แล้วตรวจพอร์ตตัวแทนด้วยข้อมูลที่ยังไม่ใช้เลือก
---

# จัดกลุ่มสินทรัพย์และเลือกตัวแทน

<p class="lead">ถ้า A กับ B ขึ้นลงคล้ายกันมาก การเลือกทั้งคู่กับการเลือกหุ้นจากคนละกลุ่มอาจให้พอร์ตต่างกัน เราจะวัดคำว่า “คล้าย” จัดกลุ่ม และตรวจว่าการเลือกตัวแทนเปลี่ยนความเสี่ยงอย่างไร</p>

Clustering เป็นการแบ่งวัตถุเป็นกลุ่มจากข้อมูลที่เลือกใช้ โดยไม่มีป้ายคำตอบว่าตัวไหนควรอยู่กลุ่มใด ในบทนี้วัตถุคือสินทรัพย์ และข้อมูลของแต่ละสินทรัพย์คือประวัติผลตอบแทน งานจัดกลุ่มสัปดาห์ที่ตลาดมีพฤติกรรมคล้ายกันกับงานจัดกลุ่มหุ้นที่เคลื่อนไหวคล้ายกันใช้ตารางเดียวกันได้ แต่ต้องสลับความหมายของแถวกับคอลัมน์

[บท PCA](pca-diversification.html) เปลี่ยนสินทรัพย์เป็นแกนผสมใหม่ ส่วนบทนี้ยังต้องการชื่อสินทรัพย์จริงสำหรับพอร์ต จึงต้องมีกฎเลือกตัวแทนจากกลุ่มต่ออีกขั้น เราจะใช้ข้อมูลสมมติ A–F ชุดเดิม แต่ใส่โค้ดสร้างข้อมูลใหม่ให้รันหน้านี้จาก Notebook ว่างได้ด้วย NumPy, pandas, SciPy และ scikit-learn

เนื้อหาเชื่อมกับ [Role of clustering](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/zBksE/role-of-clustering) และ [Lab Graphical Network Analysis](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/2vcIt/lab-session-graphical-network-analysis) ซึ่งใช้ Affinity Propagation การเปรียบเทียบวิธีและพอร์ตด้านล่างเขียนขึ้นใหม่จากข้อมูลจำลอง ไม่ใช่ผลจากหุ้น 22 บริษัทใน Lab

<span id="clustering-data-orientation"></span>

## กำหนดก่อนว่ากำลังจัดกลุ่มอะไร

ข้อมูลมี 260 สัปดาห์กับหกสินทรัพย์ ใช้สัปดาห์ 1–208 จัดกลุ่ม และเก็บ 209–260 ไว้ดูผลภายหลัง ทุกสัปดาห์สุ่มจาก Gaussian ที่มีค่าเฉลี่ย 0.001 ต่อสินทรัพย์ และ covariance คงที่ตามโค้ด ผลตอบแทนหน่วยทศนิยม ไม่ใช่ราคา

```python
import numpy as np
import pandas as pd
import warnings
from itertools import combinations
from scipy.spatial.distance import squareform, pdist
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.cluster import KMeans, AffinityPropagation
from sklearn.exceptions import ConvergenceWarning

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

`train.shape` เป็น `(208, 6)` เพราะขณะนี้แต่ละแถวยังเป็นสัปดาห์ ถ้าส่งตารางนี้ตรง ๆ ให้ clustering ที่มองแถวเป็นตัวอย่าง จะได้กลุ่มของสัปดาห์ เราต้องสร้างตารางที่มีหกแถวซึ่งแต่ละแถวแทนสินทรัพย์หนึ่งตัวก่อน

เมทริกซ์ `true_precision` ใช้กำหนดโครงสร้างการสุ่มที่รู้คำตอบไว้ล่วงหน้า โค้ดกลับเป็น covariance แล้วปรับ SD ให้ต่างกันตาม `weekly_sd` รายละเอียดของ precision จะอยู่ใน [บทเครือข่าย](asset-networks.html) การเลือกกลุ่มด้านล่างใช้เฉพาะ `train` และไม่ได้รับเมทริกซ์ประชากรนี้เป็นคำตอบ

<span id="correlation-distance"></span>

## จาก correlation เป็นระยะห่าง

ถ้าต้องการจัดกลุ่มตามรูปแบบการขึ้นลง โดยไม่ให้หุ้นที่แกว่งแรงครอบงำระยะห่าง ให้หักค่าเฉลี่ยและหาร sample SD รายสินทรัพย์ก่อน เรียกข้อมูลที่ปรับแล้วว่า $z_{ti}$ จากนั้นใช้

$$d_{ij}=\sqrt{\frac{1-\rho_{ij}}{2}}.$$

เมื่อ correlation เท่ากับ 1 ระยะเป็น 0 เมื่อ correlation เท่ากับ 0 ระยะประมาณ 0.7071 และเมื่อ correlation เท่ากับ −1 ระยะเป็น 1 หุ้นที่ขึ้นลงสวนกันจึงอยู่ห่างกันภายใต้นิยามนี้ แม้คู่ที่สวนกันอาจมีประโยชน์ต่อการลด variance ของพอร์ต

ระยะนี้สัมพันธ์กับ Euclidean distance ของประวัติที่ปรับหน่วยแล้ว ถ้าแต่ละคอลัมน์มี sample SD หนึ่ง

$$\sum_t(z_{ti}-z_{tj})^2=2(T-1)(1-\rho_{ij}).$$

ดังนั้นใช้เวกเตอร์คุณลักษณะของสินทรัพย์ $i$ เป็น $z_{\cdot i}/[2\sqrt{T-1}]$ จะได้ระยะ Euclidean ตรงกับ $d_{ij}$ ข้างต้น

```python
centered = train.to_numpy() - train.mean().to_numpy()
z = centered / train.std(ddof=1).to_numpy()
correlation = z.T @ z / (len(train) - 1)
distance = np.sqrt(np.clip((1 - correlation) / 2, 0, 1))
np.fill_diagonal(distance, 0)
asset_features = z.T / (2 * np.sqrt(len(train) - 1))
print(pd.DataFrame(distance, index=assets, columns=assets).round(3))
assert np.allclose(squareform(pdist(asset_features)), distance)
```

`z.T` เปลี่ยนเป็นหกแถว หนึ่งแถวต่อสินทรัพย์ และ 208 คอลัมน์ตามประวัติสัปดาห์ `pdist` คำนวณระยะระหว่างแถว ส่วน `squareform` แปลงรายการระยะกลับเป็นตารางสมมาตร โค้ดตรวจว่าค่าตรงกับสูตร correlation

ระยะ A/B ประมาณ 0.4641, C/D ประมาณ 0.5081 และ E/F ประมาณ 0.5210 ขณะที่ A/E ประมาณ 0.7591 การมองตารางจึงเริ่มเห็นคู่ที่เคลื่อนไหวคล้ายกัน `np.clip` จำกัดความคลาดเคลื่อนเล็กน้อยจากเลขทศนิยมให้อยู่ในช่วงที่สูตรถอดรากได้ ไม่ได้ซ่อม correlation matrix ที่ผิดจากข้อมูลสูญหายหรือการจับเวลาไม่ตรงกัน

ถ้าใช้ $|\rho|$ แทน $\rho$ จะมองหุ้นที่สวนกันว่าใกล้กัน นั่นเป็นคำถามอีกแบบหนึ่งและไม่ควรเปลี่ยนโดยไม่อธิบาย งานนี้ต้องการให้สินทรัพย์ในกลุ่มขึ้นลงไปทางเดียวกัน จึงใช้ correlation ที่ยังรักษาเครื่องหมาย

<span id="medoid-selection"></span>

## Medoid เป็นสมาชิกจริงที่ใช้แทนกลุ่ม

สมมติต้องการตัวแทนสามตัว เราเลือกชุด $M$ ที่มีสามสินทรัพย์ แล้วให้สินทรัพย์แต่ละตัวอยู่กับตัวแทนที่ใกล้ที่สุด เป้าหมายคือทำให้ผลรวมระยะถึงตัวแทนต่ำที่สุด

$$\min_{M:\,|M|=3}\sum_{i=1}^6\min_{j\in M}d_{ij}.$$

ตัวแทนที่เป็นสมาชิกจริงเรียกว่า medoid ตัวอย่างหกสินทรัพย์มีชุดให้ลองเพียง $\binom63=20$ ชุด จึงตรวจครบได้ หากมีสินทรัพย์หลายพันตัว การไล่ทุกชุดแบบนี้จะโตเร็วมากและไม่ใช่แนวทางที่ควรนำไปใช้ตรง ๆ

```python
def exact_medoids(distance_matrix, k):
    d = np.asarray(distance_matrix, dtype=float)
    if d.ndim != 2 or d.shape[0] != d.shape[1] or not np.isfinite(d).all():
        raise ValueError('Use a finite square distance matrix')
    if not np.allclose(d, d.T) or np.any(d < 0) or not np.allclose(np.diag(d), 0):
        raise ValueError('Distances must be symmetric, nonnegative, with zero diagonal')
    if isinstance(k, bool) or not isinstance(k, (int, np.integer)) or not 1 <= k <= len(d):
        raise ValueError('k must be an integer from 1 to the number of assets')
    candidates = list(combinations(range(len(d)), k))
    costs = [np.min(d[:, candidate], axis=1).sum() for candidate in candidates]
    best_cost = min(costs)
    chosen = next(i for i, cost in enumerate(costs) if cost <= best_cost + 1e-12)
    medoids = np.array(candidates[chosen])
    labels = np.argmin(d[:, medoids], axis=1)
    return medoids, labels, float(min(costs))

medoids, medoid_labels, medoid_cost = exact_medoids(distance, 3)
print('Representatives:', assets[medoids])
print('Assignments:', medoid_labels)
print('Sum of distances:', medoid_cost)
```

`combinations` สร้างชุดตัวแทนโดยไม่ซ้ำ `d[:, candidate]` เลือกคอลัมน์ของตัวแทน แล้ว `min(..., axis=1)` หาตัวที่ใกล้ที่สุดสำหรับแต่ละสินทรัพย์ ตัวอย่างได้ตัวแทน A, C, E มี assignments `[0, 0, 1, 1, 2, 2]` และผลรวมระยะประมาณ 1.49320953 ป้าย 0/1/2 เป็นหมายเลขกลุ่ม ไม่มีความหมายว่ากลุ่ม 2 เสี่ยงกว่ากลุ่ม 0

ภายในกลุ่มที่มีเพียงคู่เดียว เช่น A/B เลือก A หรือ B เป็น medoid อาจให้ผลรวมระยะเท่ากัน โค้ดเลือกชุดที่มาก่อนตามลำดับดัชนีเมื่อ objective ต่างกันไม่เกิน $10^{-12}$ เป็นกฎแก้เสมอที่กำหนดไว้ก่อนอ่านผลตอบแทนท้ายชุด จึงไม่ได้เลือก A เพราะรู้ล่วงหน้าว่า A จะให้กำไรดีกว่า B

แบบจำลอง integer optimization ที่กล่าวในบทเรียนคอร์สก็มีเจตนาเลือกตัวแทนจริงและกำหนดจำนวนกลุ่มเช่นนี้ แต่ขนาดโจทย์ที่แก้ได้ขึ้นกับข้อมูล วิธีแก้ และทรัพยากรคอมพิวเตอร์ จึงไม่ควรนำจำนวนตัวแปรหนึ่งค่ามารับรองความเร็วของทุกปัญหา

<span id="kmeans-centroid"></span>

## K-means ใช้จุดเฉลี่ยซึ่งอาจไม่มีสินทรัพย์นั้นอยู่จริง

K-means แบ่งเป็น $K$ กลุ่มแล้วลดผลรวมระยะกำลังสองจากสมาชิกไปยังค่าเฉลี่ยของกลุ่ม

$$\sum_{g=1}^K\sum_{i\in g}\|x_i-m_g\|^2,$$

โดย $m_g$ คือ centroid ของกลุ่ม ถ้ากลุ่มมีสินทรัพย์ A/B centroid คือค่าเฉลี่ยของเวกเตอร์ประวัติสองตัวนี้ ซึ่งอาจไม่มีสินทรัพย์ซื้อขายที่ให้เวกเตอร์ตรงกัน ถ้าต้องการชื่อหุ้นจริง เราต้องเลือกสมาชิกที่ใกล้ centroid ต่ออีกขั้น

```python
kmeans = KMeans(n_clusters=3, n_init=20, random_state=7).fit(asset_features)
kmeans_representatives = []
for group in range(3):
    members = np.flatnonzero(kmeans.labels_ == group)
    errors = np.sum((asset_features[members] - kmeans.cluster_centers_[group]) ** 2, axis=1)
    kmeans_representatives.append(int(members[np.argmin(errors)]))
print('K-means labels:', kmeans.labels_)
print('Nearest actual assets:', assets[kmeans_representatives])
print('Squared-distance objective:', kmeans.inertia_)
```

`n_clusters=3` กำหนดจำนวนกลุ่มล่วงหน้า `n_init=20` ให้ลองจุดเริ่มต้นหลายครั้ง และ `random_state=7` ทำให้สุ่มซ้ำได้ ชุดนี้แยกเป็น AB/CD/EF เหมือนตัวอย่าง medoids แต่ objective `inertia_` ประมาณ 0.37250073 เป็นผลรวม squared distances จึงนำไปเทียบตรง ๆ กับผลรวมระยะ 1.49320953 ของ medoids ไม่ได้

การเริ่มหลายครั้งลดโอกาสค้างที่คำตอบไม่ดี แต่ไม่ได้พิสูจน์ว่า k-means พบ global optimum เสมอไป และแม้ได้กลุ่มเดียวกัน วิธีเลือกตัวแทนภายในกลุ่มอาจให้คนละชื่อเมื่อระยะเกือบเท่ากัน สำหรับงานจริงยังต้องตรวจค่าซื้อขาย สภาพคล่อง และข้อจำกัดของสินทรัพย์ที่เลือก

<span id="hierarchical-linkage"></span>

## Hierarchical clustering บันทึกว่ารวมกลุ่มตามลำดับไหน

อีกวิธีเริ่มจากสินทรัพย์ละกลุ่ม แล้วค่อยรวมกลุ่มที่ใกล้กัน เราจะใช้ average linkage ซึ่งนิยามระยะระหว่างสองกลุ่มเป็นค่าเฉลี่ยของระยะทุกคู่ข้ามกลุ่ม วิธีนี้จึงเก็บลำดับการรวมเป็นต้นไม้และเลือกตัดจำนวนกลุ่มภายหลังได้

```python
condensed_distance = squareform(distance, checks=True)
linkage_matrix = linkage(condensed_distance, method='average')
hierarchical_labels = fcluster(linkage_matrix, t=3, criterion='maxclust')
print('Average-linkage labels:', hierarchical_labels)
print('Merge distances:', np.round(linkage_matrix[:, 2], 4))
```

`linkage` รับเวกเตอร์ระยะครึ่งบนของเมทริกซ์ที่ `squareform` เตรียมให้ ถ้าส่งเมทริกซ์ระยะ $6\times6$ ตรง ๆ ฟังก์ชันอาจตีความแต่ละแถวเป็นเวกเตอร์คุณลักษณะ แล้วคำนวณระยะใหม่ซ้ำซ้อนกับสิ่งที่ตั้งใจ

ลำดับ merge distances ในชุดนี้ประมาณ 0.4641, 0.5081, 0.5210, 0.6817 และ 0.7041 เมื่อตัดให้ได้ไม่เกินสามกลุ่ม จะได้ AB/CD/EF อีกครั้ง ป้าย `[1,1,2,2,3,3]` ใช้เลขเริ่มที่ 1 จึงต่างจากเลขป้ายของวิธีอื่น แต่สมาชิกกลุ่มเหมือนกัน

Single linkage ใช้คู่ที่ใกล้ที่สุดระหว่างกลุ่มและอาจต่อเป็นสายยาว ส่วน complete linkage ใช้คู่ที่ไกลที่สุด Ward linkage ลดการเพิ่มขึ้นของผลรวมระยะกำลังสองและต้องมีเรขาคณิตแบบ Euclidean ที่สอดคล้องกัน อย่าเลือก Ward เพียงเพราะมีตารางตัวเลขที่เรียกว่า distance โดยไม่ตรวจนิยาม [SciPy linkage](https://docs.scipy.org/doc/scipy/reference/generated/scipy.cluster.hierarchy.linkage.html)

<span id="affinity-propagation"></span>

## Affinity Propagation ให้ตัวแทนผ่าน similarity และ preference

Lab ของคอร์สใช้ Affinity Propagation ซึ่งค้นหา exemplars ที่เป็นข้อมูลจริง โดยให้แต่ละจุดส่งค่าที่เรียกว่า responsibility และ availability ระหว่างกัน Responsibility สรุปว่าจุดหนึ่งเหมาะจะเลือกอีกจุดเป็นตัวแทนเพียงใดเมื่อเทียบกับตัวเลือกอื่น ส่วน availability สรุปว่าตัวแทนที่เสนอได้รับการสนับสนุนจากจุดอื่นมากเพียงใด

เราไม่ต้องระบุ `n_clusters` แต่ยังมีทางเลือกที่ส่งผลต่อจำนวนกลุ่มคือ preference ของการเป็นตัวแทน ค่าที่มากขึ้นทำให้การตั้งตัวแทนมีความน่าสนใจมากขึ้น อีกพารามิเตอร์คือ damping ซึ่งผสมค่ารอบก่อนกับค่ารอบใหม่เพื่อลดการแกว่งของการคำนวณ ไม่ควรสรุปว่าค่า damping ต่ำกว่าจะลู่เข้าเร็วกว่าหรือดีกว่าเสมอ [เอกสาร AffinityPropagation](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.AffinityPropagation.html)

ฟังก์ชันต้องการ similarity ที่มากหมายถึงคล้ายกัน จึงใช้ $s_{ij}=-d_{ij}^2$ คู่ที่เหมือนกันมากมีค่าเข้าใกล้ศูนย์ คู่ที่ไกลกันมากมีค่าติดลบมากกว่า การส่งระยะบวกตรง ๆ จะกลับความหมาย

```python
similarity = -(distance ** 2)
ap_results = []
ap_models = {}
for preference in [-.7, -.4, -.1]:
    with warnings.catch_warnings():
        warnings.simplefilter('error', ConvergenceWarning)
        model = AffinityPropagation(affinity='precomputed', preference=preference,
                                   damping=.8, max_iter=1000, random_state=7).fit(similarity)
    ap_models[preference] = model
    ap_results.append({'preference': preference, 'clusters': len(model.cluster_centers_indices_),
                       'exemplars': ','.join(assets[model.cluster_centers_indices_])})
print(pd.DataFrame(ap_results).to_string(index=False))
ap_model = ap_models[-.4]
```

Preference −0.7, −0.4 และ −0.1 ให้ 2, 3 และ 6 กลุ่มตามลำดับในตัวอย่างนี้ ค่า −0.4 แยกเป็น AB/CD/EF เราเลือกค่านี้เพื่อแสดงกลุ่มสามคู่ที่อ่านง่าย ไม่ได้เลือกจากกำไรใน test set การเลือกจำนวนกลุ่มแบบ “อัตโนมัติ” จึงยังขึ้นกับสเกล similarity และ preference ที่เรากำหนด

`warnings.simplefilter('error', ConvergenceWarning)` ให้การคำนวณหยุดถ้าไม่ลู่เข้า แทนการนำ labels ที่ได้จากรอบที่ยังไม่นิ่งมาใช้ต่อ ชื่อ exemplar ภายในคู่ที่ใกล้เคียงกันอาจต่างตามรายละเอียดการคำนวณหรือรุ่นของไลบรารี ควรเปรียบเทียบทั้งสมาชิกกลุ่มและกฎเลือกตัวแทน ไม่ใช้หมายเลข labels เป็นรหัสธุรกิจถาวร

<span id="pca-before-clustering"></span>

## ลดมิติก่อนจัดกลุ่มจะเปลี่ยนระยะที่กำลังเปรียบเทียบ

ถ้ามีประวัติหลายปี แต่ละสินทรัพย์จะเป็นจุดที่มีหลายร้อยมิติ PCA ช่วยสร้างพิกัดที่สั้นลงได้ แต่ต้องระวังการสลับแถวคอลัมน์ เราต้องการพิกัดของสินทรัพย์หกตัว ไม่ใช่ตาราง scores ของทุกสัปดาห์

สำหรับ correlation matrix $C=U\Lambda U^\top$ พิกัดเต็มของสินทรัพย์ที่ให้ระยะ $\sqrt{(1-\rho)/2}$ คือแถวของ $U\Lambda^{1/2}/2$ เพราะ squared distance ระหว่างแถว $i,j$ เท่ากับ $(C_{ii}+C_{jj}-2C_{ij})/4=(1-\rho_{ij})/2$ หากเก็บแค่สองคอลัมน์จะได้แผนที่สองมิติ แต่ระยะบางส่วนถูกทิ้งไป

```python
corr_values, corr_vectors = np.linalg.eigh(correlation)
corr_values, corr_vectors = corr_values[::-1], corr_vectors[:, ::-1]
full_asset_coordinates = corr_vectors * np.sqrt(np.maximum(corr_values, 0)) / 2
two_pc_coordinates = full_asset_coordinates[:, :2]
full_distances = squareform(pdist(full_asset_coordinates))
two_pc_distances = squareform(pdist(two_pc_coordinates))
print('Full PCA preserves distances:', np.allclose(full_distances, distance))
print('Largest distance loss in 2D:', np.max(distance - two_pc_distances))
assert np.all(two_pc_distances <= distance + 1e-12)
```

พิกัดครบหกแกนรักษาระยะเดิมได้ ส่วนพิกัดสองแกนทำให้ระยะบางคู่หดลงมากที่สุดประมาณ 0.4528 ภายใต้สเกลระยะ 0 ถึง 1 การจัดกลุ่มบนพิกัดสองแกนจึงอาจต่างจากการจัดกลุ่มบนข้อมูลครบ แม้ภาพสองมิติจะอ่านง่ายกว่า

การคัดจำนวน PC เพื่อบีบอัดข้อมูลและการกำหนดจำนวนกลุ่มเป็นคนละพารามิเตอร์ ไม่จำเป็นต้องเลือกทั้งคู่เป็นสาม หากต้องการใช้การบีบอัดเพื่อการลงทุน ต้องเลือกเกณฑ์จากอดีตและตรวจว่าผลการจัดกลุ่มไวต่อการเพิ่มหรือลด PC เพียงใด

<span id="cluster-representative-portfolio"></span>

## ตัวแทนของกลุ่มยังต้องมีกฎลงเงิน

การเลือก medoids ให้ A/C/E ยังไม่ได้ให้น้ำหนักพอร์ต เราจะทดลองลงเท่ากันตัวละ $1/3$ แล้วเทียบกับลง A–F ตัวละ $1/6$ โดยใช้ covariance จากข้อมูลฝึกชุดเดียวกัน

```python
all_weights = np.full(6, 1 / 6)
selected_weights = np.zeros(6)
selected_weights[medoids] = 1 / len(medoids)
train_cov = train.cov().to_numpy()
training_vol = np.sqrt(52 * np.array([
    all_weights @ train_cov @ all_weights,
    selected_weights @ train_cov @ selected_weights
]))
print(pd.DataFrame({'All assets': all_weights, 'Selected': selected_weights}, index=assets))
print('Training annualized SD:', training_vol)
print('Selected ENC:', 1 / np.sum(selected_weights ** 2))
```

พอร์ตตัวแทนมี ENC เท่ากับ 3 และ SD ที่ annualize จากข้อมูลฝึกประมาณ 10.8458% ส่วนพอร์ตครบหกตัวประมาณ 9.8606% การเลือกหุ้นจากคนละกลุ่มจึงไม่ได้ทำให้ variance ต่ำลงโดยอัตโนมัติ เพราะเราตัดสมาชิกที่ช่วยเฉลี่ยความเสี่ยงภายในกลุ่มออก และเปลี่ยนน้ำหนักกับ SD รายตัวพร้อมกัน

การลงเงินเท่ากันทุกกลุ่มก็มีความหมายต่างจากลงเท่ากันทุกสินทรัพย์ ถ้ากลุ่มหนึ่งมีสี่หุ้น อีกกลุ่มมีสองหุ้น และลงแต่ละกลุ่มครึ่งพอร์ต สมาชิกกลุ่มแรกที่แบ่งเงินเท่ากันจะได้ตัวละ $1/8$ ส่วนกลุ่มหลังได้ตัวละ $1/4$ วิธีนี้ทำให้กลุ่มมีเงินเท่ากัน แต่ยังไม่ได้ทำให้แต่ละกลุ่มมี risk contribution เท่ากัน

<span id="clustering-heldout"></span>

## เปิดดู 52 สัปดาห์ที่เก็บไว้

กำหนดรายชื่อและน้ำหนักจากข้อมูล 208 สัปดาห์แรกให้เสร็จแล้ว จึงคำนวณผลในสัปดาห์ 209–260 สมมติปรับกลับสู่น้ำหนักเป้าหมายทุกต้นสัปดาห์ ซื้อขายได้ตามน้ำหนัก และไม่มีต้นทุน ดังนั้นผลตอบแทนแต่ละสัปดาห์เป็น $w^\top R_t$ การคูณผลตอบแทนกับน้ำหนักคงที่ทุกแถวหมายถึงนโยบาย rebalancing นี้ ไม่ใช่ซื้อครั้งเดียวแล้วปล่อยน้ำหนัก drift

```python
heldout_returns = pd.DataFrame({
    'All 6': test.to_numpy() @ all_weights,
    '3 medoids': test.to_numpy() @ selected_weights
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

พอร์ตครบหกตัวมีผลตอบแทน 52 สัปดาห์ประมาณ 24.306% และ SD annualized 10.470% ส่วนพอร์ตสาม medoids มีผลตอบแทนประมาณ 22.117% และ SD 10.524% ด้าน max drawdown กลับเป็นพอร์ต medoids ที่ขาดทุนน้อยกว่าในเส้นทางนี้ ประมาณ −4.377% เทียบกับ −5.621% การจัดอันดับจึงขึ้นกับมาตรวัดที่ใช้ด้วย

แถวเริ่มต้นของ `heldout_wealth` เป็น 1 ณ สิ้นสัปดาห์ 208 ก่อนลงทุน เพื่อให้ drawdown นับการขาดทุนจากเงินต้นได้ตั้งแต่งวดแรก SD คูณ $\sqrt{52}$ ภายใต้สมมติฐานรายสัปดาห์ที่ใช้เปรียบเทียบนี้ ส่วน max drawdown เป็นค่าของเส้นทาง 52 สัปดาห์และไม่ได้ annualize

ผลหนึ่งเส้นทางไม่ตัดสินว่าวิธีใดเหนือกว่าในตลาด และผลนี้ยังไม่รวมค่าซื้อขาย ดู [การทดสอบพอร์ตพร้อมบัญชีต้นทุน](diversification-backtest.html) เมื่อต้องการต่อจากตัวอย่างนี้ไปเป็น backtest ที่ปรับน้ำหนักและคิดค่าซื้อขายจริงตามสมมติฐาน

<span id="clustering-timing-check"></span>

## ตรวจว่ารายชื่อไม่ได้เปลี่ยนเพราะอนาคต

การตรวจช่วงฝึกไม่ได้จบที่อ่านตำแหน่ง `iloc` เราสามารถแก้ทุกผลตอบแทนในช่วงท้ายเป็น −10% แล้วคำนวณการเลือกจากอดีตซ้ำ ถ้ากฎใช้เฉพาะอดีตจริง รายชื่อควรเท่าเดิม

```python
future_changed = returns.copy()
future_changed.iloc[208:, :] = -.10
changed_corr = future_changed.iloc[:208].corr().to_numpy()
changed_distance = np.sqrt(np.clip((1 - changed_corr) / 2, 0, 1))
np.fill_diagonal(changed_distance, 0)
changed_medoids, _, _ = exact_medoids(changed_distance, 3)
print('Past-only selection unchanged:', np.array_equal(changed_medoids, medoids))
assert np.array_equal(changed_medoids, medoids)
```

ผลเป็น `True` การทดสอบนี้ตรวจการแบ่งเวลาในโค้ดตัวอย่าง แต่ข้อมูลจริงยังต้องมีรายชื่อหลักทรัพย์ที่รู้ได้ ณ วันตัดสินใจ วันที่ข้อมูลเผยแพร่ และวิธีจัดการหุ้นที่เลิกกิจการ การเลือกเฉพาะบริษัทที่ยังอยู่รอดจนวันสุดท้ายก่อนย้อนทดสอบจะทำให้เกิด survivorship bias แม้ index slicing จะเขียนถูกต้อง

Correlation ต้องใช้ช่วงเวลาเดียวกันของแต่ละคู่ การแทนค่าหายด้วยศูนย์แปลว่าสมมติผลตอบแทนศูนย์ ส่วนการลบทุกหุ้นที่มีข้อมูลหายอาจเปลี่ยน universe ไปมาก จึงควรรายงานเหตุผลและจำนวนข้อมูลที่เหลือก่อนตีความ clusters

<span id="clustering-exercises"></span>

## แบบฝึกหัดพร้อมเฉลย

1. คู่หนึ่งมี correlation 0.5 อีกคู่มี −0.5 จงคำนวณระยะตามสูตรในบท

<details><summary>เฉลยข้อ 1</summary>

คู่แรกมีระยะ $\sqrt{(1-0.5)/2}=0.5$ คู่หลังมีระยะ $\sqrt{(1+0.5)/2}\approx0.866025$ จึงอยู่ห่างกว่า สูตรนี้จัดกลุ่มตามทิศทางขึ้นลงที่คล้ายกัน ไม่ได้ให้คะแนนประโยชน์การ hedge โดยตรง

</details>

2. มีข้อมูล 100 สัปดาห์และ 20 หุ้น ถ้าจะให้ k-means จัดกลุ่มหุ้น ตารางคุณลักษณะควรมีกี่แถว

<details><summary>เฉลยข้อ 2</summary>

ต้องมี 20 แถว หนึ่งแถวต่อหุ้น ส่วนคอลัมน์อาจเป็นประวัติ 100 สัปดาห์ที่ปรับหน่วยแล้ว หรือพิกัดที่ลดมิติจากประวัตินั้น หากส่งตาราง 100 แถวตรง ๆ จะจัดกลุ่มสัปดาห์

</details>

3. ทำไม centroid จึงไม่รับรองว่าจะซื้อเป็นหลักทรัพย์หนึ่งตัวได้

<details><summary>เฉลยข้อ 3</summary>

Centroid เป็นค่าเฉลี่ยของเวกเตอร์คุณลักษณะ อาจไม่ตรงกับสมาชิกตัวใด จึงต้องเลือกสมาชิกใกล้ centroid หรือกำหนดพอร์ตผสมสมาชิกต่างหาก ส่วน medoid และ exemplar ต้องเป็นสมาชิกจริงตั้งแต่ต้น

</details>

4. Affinity Propagation ไม่รับ `n_clusters` แปลว่าไม่มีพารามิเตอร์ที่มีผลต่อจำนวนกลุ่มหรือไม่

<details><summary>เฉลยข้อ 4</summary>

ยังมี preference และนิยาม similarity ซึ่งมีผลต่อจำนวน exemplar ตัวอย่างนี้เปลี่ยน preference อย่างเดียวก็ได้ 2, 3 และ 6 กลุ่ม การตั้งค่าอัตโนมัติของบางขั้นไม่ทำให้การเลือกแบบจำลองหายไป

</details>

5. สองกลุ่มมีสมาชิก 3 และ 1 ตัว ถ้าแบ่งเงินเท่ากันสองกลุ่มแล้วแบ่งเท่ากันภายในกลุ่ม น้ำหนักรายตัวและ ENC เป็นเท่าไร

<details><summary>เฉลยข้อ 5</summary>

น้ำหนักคือ $(1/6,1/6,1/6,1/2)$ ทำให้ $\sum_iw_i^2=3/36+1/4=1/3$ จึงมี ENC เท่ากับ 3 แม้ถือสี่ชื่อ ส่วน risk contribution ต้องใช้ covariance เพิ่ม

</details>

6. เลือก preference ที่ให้ผลตอบแทนดีที่สุดในสัปดาห์ 209–260 แล้วรายงานผลช่วงนี้ว่า out-of-sample ได้หรือไม่

<details><summary>เฉลยข้อ 6</summary>

ช่วงนั้นถูกใช้เลือกพารามิเตอร์แล้ว จึงทำหน้าที่เป็น validation ไม่ใช่ test ที่ไม่เคยเห็น ต้องเก็บข้อมูลอีกช่วงไว้ประเมิน หรือใช้กระบวนการเดินเวลาโดยเลือกพารามิเตอร์ภายในข้อมูลอดีตของแต่ละรอบก่อนตัดสินใจ

</details>

<span id="clustering-sources"></span>

## แหล่งที่มาและขอบเขตการอ่าน

อ่าน transcript เต็มของ Role of clustering และ Lab Graphical Network Analysis เมื่อ 3 ตุลาคม 2026 บทแรกอธิบายการเลือกตัวแทนด้วยโจทย์จำนวนเต็ม ส่วน Lab อธิบาย Affinity Propagation ร่วมกับ Graphical Lasso และ MDS ไม่ได้รันหรือเผยแพร่โค้ดของผู้สอน ตัวอย่าง medoids แบบตรวจครบ 20 ชุด, average linkage และ holdout ในหน้านี้เป็นส่วนที่เขียนเพิ่มเพื่อสอนการตรวจคำตอบ

ตรวจรูปแบบ input และ linkage จากเอกสาร SciPy และตรวจ similarity, preference, damping และ convergence จากเอกสาร scikit-learn ที่ลิงก์ไว้ข้างต้น รันตัวอย่างด้วย NumPy 2.0.2, pandas 2.3.3, SciPy 1.13.1 และ scikit-learn 1.6.1 ชื่อกลุ่มและตัวแทนที่เสมอกันอาจเปลี่ยนตามรายละเอียดการคำนวณ โดยไม่เปลี่ยนคำถามทางสถิติที่กำลังตอบ
