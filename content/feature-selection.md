---
title: "เลือก Feature และตรวจความเสถียร"
description: เปรียบเทียบการเลือกตัวแปรด้วย validation ตามเวลา แยกค่าความสำคัญจากเหตุและผล แล้วตรวจ collinearity, block permutation และข้อจำกัดการเลือกซ้ำ
---

# เลือก Feature และตรวจความเสถียร

<p class="lead">ถ้าเอาคอลัมน์หนึ่งออกแล้วโมเดลยังทายได้ใกล้เดิม คอลัมน์นั้นไม่มีข้อมูล หรือมีคอลัมน์อื่นบอกเรื่องเดียวกันอยู่แล้ว?</p>

การมี feature มากขึ้นเพิ่มทั้งโอกาสพบข้อมูลที่ใช้พยากรณ์และโอกาสจำ noise บทนี้ใช้ข้อมูลเดียวกับ [Lab พยากรณ์เหตุการณ์](recession-models.html) เพื่อดูขั้นตอนเลือกตัวแปรให้ชัด เราจะเลือกจาก validation ตามเวลา ตรวจการพึ่งพา feature แล้วนำขั้นตอนที่ตรึงไว้ไปประเมินช่วงท้าย

ตัวอย่างทั้งหมดเป็นข้อมูลจำลอง ไม่ใช่การค้นพบตัวชี้นำเศรษฐกิจจริง การใช้ข้อมูลเดิมซ้ำในหลายบทเป็นการอธิบายวิธีคำนวณ ไม่ใช่หลักฐานจากหลายการทดลองที่เป็นอิสระต่อกัน หากนำผลช่วงท้ายมาปรับวิธีอีก ต้องมีข้อมูลใหม่สำหรับประเมินครั้งถัดไป

## Feature ที่มีประโยชน์หมายถึงอะไร

Feature อาจมีประโยชน์ต่อโมเดลหนึ่งและไม่ช่วยอีกโมเดลหนึ่ง เช่น ผลกระทบที่เกิดเมื่อสองตัวแปรร่วมกันเกินเกณฑ์อาจไม่ปรากฏใน correlation ของแต่ละคอลัมน์กับ target หรือ feature สองตัวอาจให้ข้อมูลซ้ำกันจนเอาตัวหนึ่งออกแล้วคะแนนไม่เปลี่ยน

จึงควรแยกคำถามสามแบบ:

| คำถาม | วิธีที่พอช่วยตอบได้ | สิ่งที่ยังสรุปไม่ได้ |
|---|---|---|
| คอลัมน์สัมพันธ์กับ target หรือไม่ | สถิติความสัมพันธ์ที่ระบุรูปแบบ | ความสัมพันธ์ไม่จำเป็นต้องเป็นเหตุและผล |
| โมเดลพึ่งพาคอลัมน์นี้หรือไม่ | ตรวจ coefficients, ablation หรือ permutation | โมเดลอื่นอาจใช้คอลัมน์ทดแทนได้ |
| การใส่คอลัมน์นี้ช่วยพยากรณ์ใหม่หรือไม่ | เปรียบเทียบขั้นตอนบน validation/test ที่เหมาะสม | ผลช่วงเดียวไม่รับประกันอนาคต |

Filter เลือกจากสถิติก่อนฝึกโมเดลหลัก เช่น correlation; wrapper ทดลองชุดคอลัมน์แล้วเทียบคะแนนของโมเดล; embedded method เลือกหรือหดค่าสัมประสิทธิ์ระหว่างฝึก เช่น [Lasso](regularized-factor-models.html) ทั้งสามแบบต้องอยู่ภายในขั้นฝึกของแต่ละ fold ไม่เลือกจากข้อมูลทั้งหมดก่อนแบ่งชุด

## สร้างข้อมูลที่รู้วันพร้อมใช้

ใช้ 240 เดือนสมมติ มี Indicator ที่เผยแพร่ช้าหนึ่งเดือน, Market indicator ที่รู้สิ้นเดือน, Noise และการเปลี่ยนของ Indicator ที่เผยแพร่แล้ว Target เป็นเหตุการณ์เดือนหน้า ซึ่งประกาศช้าสองเดือน จึงใช้แถวฝึกได้เมื่อ `label_available <= cutoff` ฟังก์ชันด้านล่างสร้าง fixture เดียวกับบทก่อนเพื่อให้ Notebook นี้รันแยกได้

```python
import numpy as np
import pandas as pd

def make_event_data(seed=501):
    rng=np.random.default_rng(seed)
    n=240
    signal=np.zeros(n)
    innovations=rng.normal(size=n)
    for t in range(1,n):
        signal[t]=.75*signal[t-1]+.65*innovations[t]
    probability=1/(1+np.exp(-(-1.3+1.2*signal+.5*(signal>1))))
    event=(rng.uniform(size=n)<probability).astype(int)
    # Macro series for month t arrives one month later. Dates below are ordinals.
    raw=pd.DataFrame({'month':np.arange(n),'indicator':signal+rng.normal(0,.2,n),
                      'market':signal+rng.normal(0,.6,n),
                      'noise':rng.normal(size=n),'event':event})
    x=pd.DataFrame({'indicator_lag1':raw.indicator.shift(1),
                    'market':raw.market,'noise':raw.noise})
    x['indicator_change']=x.indicator_lag1.diff()
    data=x.assign(origin=raw.month,target=raw.event.shift(-1),label_available=raw.month+3)
    return data.dropna().reset_index(drop=True)

data = make_event_data()
features = ["indicator_lag1", "market", "noise", "indicator_change"]
print("Rows:", len(data))
print(data[features + ["origin", "label_available"]].head().round(4).to_string(index=False))
```

การเพิ่ม lag หลายระยะทำให้จำนวน feature โตเร็ว หากมี 100 series และเก็บค่า ณ ปัจจุบันพร้อม lag อีกห้าระยะ จะได้ถึง 600 คอลัมน์ ก่อนนับ interactions แต่จำนวนเดือนที่มีคำตอบไม่ได้เพิ่มตามจำนวนคอลัมน์

```python
series_count = 100
lags_including_current = 6
feature_count = series_count * lags_including_current
print("Potential feature columns:", feature_count)
print("Columns per available observation:", round(feature_count / len(data), 3))
```

สัดส่วนนี้เป็นเพียงสัญญาณว่าต้องระวังความซับซ้อน ไม่ใช่กฎตัดสินตายตัวว่าใช้โมเดลไม่ได้ ข้อสมมติ โครงสร้าง regularization ความสัมพันธ์ระหว่างคอลัมน์ และจำนวนเหตุการณ์มีผลด้วย

## Coefficient เล็กไม่ได้แปลว่า Feature ไม่มีบทบาท

ลองสร้าง $x_2=2x_1$ ทุกแถว และ target $y=3x_1$ จะมี coefficients หลายคู่ที่ให้คำตอบเหมือนกัน เช่น $(3,0)$ และ $(1,1)$ เพราะ $3x_1=1x_1+1x_2$ ปัญหานี้เรียกว่า [multicollinearity](glossary.html#multicollinearity)

```python
x1 = np.array([-2., -1., 0., 1., 2.])
redundant_x = np.column_stack([x1, 2 * x1])
redundant_y = 3 * x1
coefficient_a = np.array([3., 0.])
coefficient_b = np.array([1., 1.])
print("Same predictions:", np.allclose(redundant_x @ coefficient_a,
                                         redundant_x @ coefficient_b))
print("Design rank:", np.linalg.matrix_rank(redundant_x))
print("Number of columns:", redundant_x.shape[1])
```

rank เท่ากับ 1 แม้มีสองคอลัมน์ การตัดสิน importance จาก coefficient ของคอลัมน์เดียวจึงอาจคลาดเคลื่อน และถ้าคอลัมน์ใช้หน่วยต่างกันขนาด coefficient ก็เทียบกันตรง ๆ ไม่ได้ การ standardize ช่วยเรื่องสเกล แต่ไม่ได้ทำให้ข้อมูลที่ซ้ำกันกลายเป็นอิสระ

สำหรับ Lasso คอลัมน์ที่สัมพันธ์กันมากอาจสลับกันถูกเลือกเมื่อข้อมูลเปลี่ยนเล็กน้อย ส่วน Ridge มักกระจาย coefficient ระหว่างคอลัมน์ที่สัมพันธ์กัน จึงต้องแยกความเสถียรของคำพยากรณ์ออกจากความเสถียรของรายชื่อ feature

## เลือกชุดคอลัมน์ด้วย Validation

เราจะลองทุก subset ขนาดหนึ่งถึงสามจากสี่ features ได้ทั้งหมด $\binom41+\binom42+\binom43=14$ ชุด ถ้ามี 100 features วิธีลองทุก subset ทุกขนาดต้องพิจารณา $2^{100}-1$ ชุด ซึ่งไม่ใช่ทางเลือกที่เหมาะกับคอมพิวเตอร์ทั่วไป ตัวอย่างเล็กนี้ใช้เพื่อทำให้เห็นสิ่งที่ wrapper method กำลังเปรียบเทียบ

```python
from itertools import combinations

subsets = [subset for size in (1, 2, 3) for subset in combinations(features, size)]
print("Candidate subsets:", len(subsets))
print("All non-empty subsets with 100 columns:", 2**100 - 1)
```

ใช้ Logistic settings เดียวกันทุกชุด และ Pipeline ที่ fit scaler จาก training ของแต่ละ fold เท่านั้น Validation สามช่วงคือ origin 120–139, 140–159 และ 160–177 โดย cutoff ฝึกอยู่ที่ 120, 140, 160 ตามลำดับ

```python
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

folds = [(120, 140), (140, 160), (160, 178)]

def subset_score(source, columns):
    losses = []
    for cutoff, end in folds:
        training = source[source.label_available <= cutoff]
        validation = source[(source.origin >= cutoff) & (source.origin < end)]
        model = make_pipeline(StandardScaler(), LogisticRegression(C=1, max_iter=2000))
        model.fit(training[list(columns)], training.target)
        probability = model.predict_proba(validation[list(columns)])[:, 1]
        losses.extend((probability - validation.target.to_numpy()) ** 2)
    return float(np.mean(losses))

subset_results = sorted([(subset_score(data, subset), subset) for subset in subsets],
                        key=lambda item: (item[0], item[1]))
subset_table = pd.DataFrame(subset_results, columns=["validation_brier", "features"])
print(subset_table.head(8).to_string(index=False))
selected_features = list(subset_results[0][1])
```

ชุดที่ได้ Brier ต่ำสุดใน fixture นี้คือ `indicator_lag1` เพียงตัวเดียว ได้ประมาณ 0.184627 ชุด `indicator_lag1, market` ได้ประมาณ 0.185154 ต่างกันประมาณ 0.000528 การเลือกจากค่าต่ำสุดทำตามกฎที่ตั้งไว้ แต่ความต่างเล็กน้อยนี้ไม่ใช่หลักฐานว่า Market indicator ไม่มีข้อมูล

ยิ่งลองหลายชุด โอกาสได้คะแนน validation ดีเพราะความบังเอิญก็เพิ่มขึ้นด้วย หากจะเปรียบเทียบกระบวนการเลือก feature หลายแบบ ต้องนำทั้งกระบวนการเข้าไปอยู่ใน inner validation แล้วประเมินด้วย outer time split หรือกันช่วงท้ายไว้จริง ๆ ตามแนวทาง [cross-validation สำหรับข้อมูลตามเวลา](https://scikit-learn.org/1.6/modules/cross_validation.html#cross-validation-of-time-series-data)

## ตรึงรายชื่อ แล้วประเมินช่วงท้าย

ต่างจาก Lab ก่อนที่ฝึกใหม่ทุกเดือน ตัวอย่างนี้ fit ครั้งเดียวที่ cutoff 180 แล้วใช้ coefficients เดิมตลอด origin 180–238 เราจึงประเมินขั้นตอนคนละแบบ ห้ามนำคะแนนทั้งสองบทมาเทียบแล้วสรุปว่า feature selection เป็นเหตุให้ดีขึ้นหรือลงโดยไม่ควบคุมความแตกต่างนี้

```python
from sklearn.metrics import brier_score_loss, log_loss

training_final = data[data.label_available <= 180]
test_final = data[data.origin >= 180]
selected_model = make_pipeline(StandardScaler(), LogisticRegression(C=1, max_iter=2000))
selected_model.fit(training_final[selected_features], training_final.target)
selected_probability = selected_model.predict_proba(test_final[selected_features])[:, 1]
constant_probability = np.repeat(training_final.target.mean(), len(test_final))
selected_test_brier = brier_score_loss(test_final.target, selected_probability)
constant_test_brier = brier_score_loss(test_final.target, constant_probability)
print("Frozen feature list:", selected_features)
print(f"Selected model Brier: {selected_test_brier:.6f}")
print(f"Training-rate baseline Brier: {constant_test_brier:.6f}")
print(f"Selected model log loss: {log_loss(test_final.target, selected_probability):.6f}")
```

ได้ Brier ประมาณ 0.181867 เทียบ baseline ประมาณ 0.184059 ความต่างเล็กและมี test เพียง 59 เดือน ซึ่งไม่เป็นอิสระกันโดยการสร้างข้อมูล การประมาณช่วงความไม่แน่นอนด้วยสูตรที่ถือว่าทุกเดือน IID จึงอาจให้ความมั่นใจเกินจริง ต้องพิจารณาความต่อเนื่องและจำนวนเหตุการณ์ด้วย

## ถ้ารบกวน Feature แล้วคะแนนแย่ลง แปลว่าอะไร

Permutation importance เป็นการตรึงโมเดล แล้วทำลายข้อมูลบางส่วนของ feature เพื่อดูว่าคะแนนแย่ลงเท่าไร เราจะใช้เฉพาะ validation สำหรับการวิเคราะห์นี้ เพื่อเก็บช่วงท้ายไว้สำหรับการรายงานกระบวนการที่ตรึงแล้ว

ข้อมูลอนุกรมเวลามีความต่อเนื่อง การสุ่มแต่ละแถวอย่างอิสระอาจสร้างชุดข้อมูลที่ไม่เหมือนสถานการณ์ใดเลย ตัวอย่างนี้สลับเป็น block ยาวหกเดือนเพื่อคงลำดับภายใน block แต่ยังทำลายความสัมพันธ์กับ target และข้ามขอบ block จึงเป็นการรบกวนเพื่อวิเคราะห์ความไว ไม่ใช่การจำลองเศรษฐกิจหรือการทดสอบเชิงเหตุและผล

```python
training_inspect = data[data.label_available <= 120]
validation_inspect = data[(data.origin >= 120) & (data.origin < 178)]
inspection_model = make_pipeline(StandardScaler(), LogisticRegression(C=1, max_iter=2000))
inspection_model.fit(training_inspect[features], training_inspect.target)
inspection_base = brier_score_loss(validation_inspect.target,
                                   inspection_model.predict_proba(validation_inspect[features])[:, 1])
blocks = [np.arange(i, min(i + 6, len(validation_inspect)))
          for i in range(0, len(validation_inspect), 6)]
print("Block lengths:", [len(block) for block in blocks])
print(f"Validation Brier before perturbation: {inspection_base:.6f}")
```

มีเก้ากลุ่มยาวหกเดือนและกลุ่มสุดท้ายยาวสี่เดือน เราสลับทั้งกลุ่มโดยไม่ทำให้แถวหายหรือซ้ำ จากนั้นทำซ้ำ 20 ครั้งด้วย seed ที่กำหนด คะแนน importance คือ Brier หลังรบกวนลบด้วย Brier เดิม ค่าบวกจึงหมายถึงโมเดลเสียความสามารถในการทำนายเมื่อ feature ถูกทำลายตามวิธีนี้

```python
rng_importance = np.random.default_rng(502)
importance_rows = []
for feature in features:
    changes = []
    for repeat in range(20):
        order = np.concatenate([blocks[i] for i in rng_importance.permutation(len(blocks))])
        permuted = validation_inspect[features].copy()
        permuted[feature] = permuted[feature].to_numpy()[order]
        probability = inspection_model.predict_proba(permuted)[:, 1]
        changes.append(brier_score_loss(validation_inspect.target, probability) - inspection_base)
    importance_rows.append({"feature": feature, "mean_loss_increase": np.mean(changes),
                            "permutation_sd": np.std(changes, ddof=1)})
importance_table = pd.DataFrame(importance_rows)
print(importance_table.round(6).to_string(index=False))
```

Indicator lag มี loss increase เฉลี่ยประมาณ 0.01307 ส่วน Noise มีค่าเฉลี่ยติดลบประมาณ −0.00235 หมายถึงรบกวน noise แล้วคะแนนของโมเดลตัวนี้บน validation นี้ดีขึ้นเล็กน้อย ไม่ได้แปลว่า feature นั้นมี “ข้อมูลติดลบ” เป็นคุณสมบัติถาวร

`permutation_sd` วัดความต่างระหว่างการรบกวน 20 ครั้งภายใต้ข้อมูลและโมเดลเดิม ไม่ใช่ standard error ของผลในตลาดทุกภาวะ ถ้า features ทดแทนกันได้ การสลับตัวเดียวอาจดูมีผลน้อยเพราะอีกตัวช่วยแทน หรืออาจสร้างค่าร่วมที่เป็นไปไม่ได้ จึงควรดูการตัดออกแล้วฝึกใหม่หรือการรบกวนทั้งกลุ่มประกอบด้วย

## ความเสถียรข้ามช่วงเวลา

ลองอ่าน coefficients ของ Pipeline ที่ใช้ทั้งสี่ features เมื่อฝึกที่ cutoff 120, 140 และ 160 ทุก coefficient เป็นผลต่อ log-odds ต่อหนึ่ง training SD ของ feature รอบนั้น การเปลี่ยน coefficient อาจมาจากทั้งข้อมูลที่เพิ่ม ความสัมพันธ์ที่เปลี่ยน และ SD ที่ใช้แปลงหน่วย

```python
coefficient_rows = []
for cutoff, _ in folds:
    training = data[data.label_available <= cutoff]
    model = make_pipeline(StandardScaler(), LogisticRegression(C=1, max_iter=2000))
    model.fit(training[features], training.target)
    coefficient_rows.append(pd.Series(model[-1].coef_[0], index=features, name=cutoff))
coefficient_history = pd.DataFrame(coefficient_rows)
print(coefficient_history.round(4).to_string())
```

อย่าอ่านการเปลี่ยนเครื่องหมายเป็นการเปลี่ยนกฎเศรษฐกิจทันที ควรตรวจขนาดผล จำนวนเหตุการณ์ ความสัมพันธ์ของตัวแปร และคุณภาพคำพยากรณ์ ถ้าต้องการเทียบ coefficients ในหน่วยดั้งเดิม ให้หารด้วย scaler ของรอบนั้นและปรับ intercept ให้สอดคล้องกัน

## ตรวจว่าการเลือกไม่แอบใช้ช่วงท้าย

แก้ features และ target ตั้งแต่ origin 180 แล้วเรียกตัวเลือกใหม่ รายชื่อและคะแนน validation ต้องเหมือนเดิม เพราะขั้นเลือกใช้เฉพาะ origin ก่อนหน้านั้นและ label ที่ประกาศก่อนแต่ละ cutoff

```python
future_changed = data.copy()
future_changed.loc[future_changed.origin >= 180, features] += 50
future_changed.loc[future_changed.origin >= 180, "target"] = 1 - future_changed.loc[
    future_changed.origin >= 180, "target"]
changed_subset_results = sorted([(subset_score(future_changed, subset), subset) for subset in subsets],
                               key=lambda item: (item[0], item[1]))
selection_unchanged = all(np.isclose(a[0], b[0]) and a[1] == b[1]
                          for a, b in zip(subset_results, changed_subset_results))
print("Selection unchanged by final-period perturbation:", selection_unchanged)
```

ผลเป็น `True` ถ้าเปลี่ยนโค้ดไปคำนวณ feature importance จากทุกแถวก่อนเลือก หรือใช้ test ตัดสิน subset เงื่อนไขนี้อาจไม่ผ่าน การตรวจด้วยการเปลี่ยนอนาคตจึงช่วยให้ข้อกำหนดเรื่องเวลาเป็นสิ่งที่ทดสอบได้ ไม่ใช่คำอธิบายลอย ๆ

## จาก Feature สู่การตัดสินใจลงทุน

โมเดลที่พยากรณ์ได้ดีขึ้นยังต้องผ่านการแปลง probability เป็นการตัดสินใจ ภายใต้วัตถุประสงค์ ความเสี่ยง ต้นทุน และข้อจำกัดของพอร์ต ลองเทียบการเปลี่ยนน้ำหนักเล็กน้อยตาม probability กับการย้ายพอร์ตทั้งหมดเมื่อข้าม threshold ทั้งสองให้ turnover และผลขาดทุนเมื่อเตือนผิดต่างกัน แม้ใช้คำพยากรณ์ชุดเดียวกัน

หากเพิ่มข้อมูลรายบุคคลหรือ alternative data ต้องรู้สิทธิในการใช้ วิธีสร้างตัวแปร และกลุ่มที่ข้อมูลครอบคลุม ข้อมูลที่มากขึ้นไม่ได้ชดเชยการตั้ง target ผิดหรือวันที่พร้อมใช้ผิด Reinforcement learning เป็นอีกแนวทางที่เรียนกฎตัดสินใจจากผลตอบรับ แต่ยังต้องระบุ reward, การเปลี่ยนสภาวะ, ต้นทุน และการประเมินนอกตัวอย่าง ไม่ใช่ขั้นตอนที่ข้ามข้อจำกัดเหล่านี้ได้

ก่อนนำผลไปสื่อสารให้แยกสามสิ่งไว้: ข้อมูลใดสังเกตได้จริง สมมติฐานใดเป็นของแบบจำลอง และข้อสรุปใดเป็นเพียงผลของการทดลองช่วงหนึ่ง ตัวอย่างบทนี้ทำให้ตรวจสองส่วนแรกได้ชัด แต่ยังไม่ให้หลักฐานสำหรับการลงทุนจริง

## แบบฝึกหัด

<details><summary>1. มี feature สองตัวที่เหมือนกันทุกแถว แล้ว Lasso เลือกเพียงตัวเดียว อีกตัวไม่มีข้อมูลหรือไม่?</summary>
<p>สรุปเช่นนั้นไม่ได้ ทั้งสองให้ข้อมูลซ้ำกัน การเลือกตัวใดตัวหนึ่งอาจขึ้นกับรายละเอียด solver หรือข้อมูลที่เปลี่ยนเล็กน้อย ควรประเมินระดับกลุ่มตัวแปรและความเสถียรของคำพยากรณ์</p>
</details>

<details><summary>2. ทำไมไม่คัด feature จาก correlation ทั้งไฟล์ก่อนแบ่งเวลา?</summary>
<p>Correlation นั้นใช้ target ในอนาคตช่วยตัดสินว่าคอลัมน์ไหนดูดี การเลือก feature จึงเห็นคำตอบชุดทดสอบแล้ว ต้องคำนวณสถิติที่ใช้เลือกภายใน training ของแต่ละ fold</p>
</details>

<details><summary>3. หากมีห้า features และลองทุก subset ขนาดหนึ่งหรือสอง มีกี่ชุด?</summary>
<p>มี 5 + 10 = 15 ชุด จาก 5 choose 1 และ 5 choose 2 หากรวมทุกขนาดตั้งแต่หนึ่งถึงห้า จะมี 2⁵−1 = 31 ชุด</p>
</details>

<details><summary>4. Permutation importance ติดลบหมายความว่า feature เป็นผลเสียเสมอหรือไม่?</summary>
<p>ไม่หมายความเช่นนั้น บอกเพียงว่าการรบกวนตามวิธีนี้ทำให้คะแนนบนชุดที่ใช้ดีขึ้น อาจมาจาก noise, overfitting, ความสัมพันธ์ของ feature หรือความบังเอิญ ต้องตรวจหลายช่วงและวิธีเปรียบเทียบอื่นประกอบ</p>
</details>

<details><summary>5. ใช้ SD ของ permutation 20 ครั้งเป็นช่วงความเชื่อมั่นของกำไรกลยุทธ์ได้หรือไม่?</summary>
<p>ไม่ได้ สิ่งที่เปลี่ยนมีเพียงการจัดข้อมูลของ feature ขณะตรึงโมเดลและตัวอย่างเดิมไว้ ไม่ได้สุ่มประวัติตลาดใหม่หรือประเมินความไม่แน่นอนของผลตอบแทนพอร์ต</p>
</details>

<details><summary>6. เพิ่ม features แล้ว validation ดีขึ้น 0.0001 จึงควรประกาศว่าโมเดลดีขึ้นแน่นอนหรือไม่?</summary>
<p>ยังไม่ได้ ต้องดูขนาดข้อมูล ความไม่แน่นอน จำนวนแบบที่ลอง ความเสถียร และผลชุดท้ายที่ไม่ใช้เลือก ความต่างเล็กหลังทดลองหลายแบบอาจเกิดจากการเลือกสิ่งที่บังเอิญทำได้ดี</p>
</details>

<details><summary>7. Feature ช่วยพยากรณ์ Recession ได้ แปลว่าควรใช้เป็นสัญญาณขายทันทีหรือไม่?</summary>
<p>ยังขาดขั้นแปลงคำพยากรณ์เป็นการตัดสินใจ ต้องตรวจเวลาส่งคำสั่ง ต้นทุน ความเสี่ยงพอร์ต สินทรัพย์ทดแทน และผลเมื่อเตือนผิด รวมทั้งทดสอบขั้นตอนทั้งหมดตามเวลา</p>
</details>

ย้อนดู [หลักการทดสอบโมเดล](model-validation.html) เมื่อจะขยายการทดลอง หรือกลับไป [Scenario Portfolio](regime-scenarios.html) เพื่อเชื่อม probability ของภาวะตลาดกับโจทย์จัดพอร์ตที่ระบุวัตถุประสงค์ไว้
