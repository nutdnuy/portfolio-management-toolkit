---
title: "ทดสอบโมเดลโดยไม่เห็นอนาคต"
description: "แยก Train, Validation และ Test ตามเวลา เลือก KNN โดยไม่แตะ Holdout ตรวจ Data Leakage และทดลอง Cross-validation, Ensemble กับ Shrinkage"
---

# ทดสอบโมเดลโดยไม่เห็นอนาคต

<p class="lead">โมเดลที่จำข้อมูลเก่าได้แม่นอาจพลาดเมื่อเจอข้อมูลใหม่ เราจะใช้วันที่กำกับทุกแถว กำหนดว่าคำตอบรู้เมื่อไร แล้วลองเลือกจำนวนเพื่อนบ้านโดยกันช่วงสุดท้ายไว้ประเมินเพียงครั้งเดียว</p>

บทนี้ต่อจาก [Regression และเพื่อนบ้าน](supervised-learning.html) โค้ดทั้งหมดใช้ข้อมูลจำลองที่สร้างขึ้นใหม่ รันเรียงใน Notebook ใหม่ได้ด้วย NumPy, pandas และ scikit-learn 1.6.1 เราจะพยากรณ์ class ว่าผลตอบแทนเดือนถัดไปเป็นบวกหรือไม่ ยังไม่สร้างกลยุทธ์ซื้อขายจากคำพยากรณ์

<span id="validation-data"></span>

## กำหนดทั้งวันที่มี Feature และวันที่รู้คำตอบ

ให้มี features สองตัวชื่อ `signal_a` และ `signal_b` เป็นคะแนนสมมติที่ไม่มีหน่วย และทราบหลังสิ้นเดือนที่ระบุใน index คำตอบ `next_positive` จะทราบหลังสิ้นเดือนถัดไป เช่น แถว 31 มกราคมใช้ทายผลของเดือนกุมภาพันธ์ จึงมี `label_known_on` เป็นวันสิ้นเดือนกุมภาพันธ์

เพื่อให้ตรวจวิธีทำงานได้ เราสร้างความน่าจะเป็นจากสูตรที่รู้แน่นอน:

$$
p_t=\frac{1}{1+\exp[-(1.2x_{t,1}-0.7x_{t,2})]}.
$$

จากนั้นสุ่มคำตอบ 0 หรือ 1 ตาม $p_t$ คะแนนสูงจึงไม่ได้บังคับว่าคำตอบต้องเป็น 1 ทุกครั้ง โมเดลจะได้รับเพียง features และคำตอบในช่วงฝึก ไม่ได้รับสูตรหรือ $p_t$ ที่ใช้สร้างโลกจำลอง

```python
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier

validation_rng = np.random.default_rng(20261003)
validation_dates = pd.date_range("2005-01-31", periods=180, freq="ME")
validation_X = validation_rng.normal(size=(180, 2))
generating_probabilities = 1 / (1 + np.exp(
    -(1.2 * validation_X[:, 0] - 0.7 * validation_X[:, 1])
))
validation_y = validation_rng.binomial(1, generating_probabilities)
validation_data = pd.DataFrame(validation_X, index=validation_dates,
                               columns=["signal_a", "signal_b"])
validation_data["next_positive"] = validation_y
validation_data["label_known_on"] = validation_dates + pd.offsets.MonthEnd(1)
print(validation_data.head(3).round(4))
```

`default_rng` สร้างเครื่องสุ่มโดยกำหนด seed ให้ทำซ้ำได้ `normal(size=(180, 2))` สร้างตารางคะแนน 180 แถว สองคอลัมน์ ส่วน `binomial(1, p)` ทดลองเหตุการณ์ที่มีโอกาสเกิด $p$ หนึ่งครั้งต่อแถว วันที่เก่าเหล่านี้เป็นป้ายกำกับตัวอย่าง ไม่มีข้อมูลตลาดปีเหล่านั้นอยู่ในตาราง

ตัวอย่างสมมติให้ความสัมพันธ์นี้คงเดิมตลอด 180 เดือน และคะแนนแต่ละแถวสุ่มอย่างอิสระ ตลาดจริงอาจมีความสัมพันธ์ข้ามเวลา ข้อมูลแก้ย้อนหลัง หรือโครงสร้างเปลี่ยน การผ่านการทดลองนี้ตรวจได้เพียงว่ากระบวนการแบ่งข้อมูลและคำนวณทำงานตามที่กำหนด

<span id="validation-split"></span>

## ให้ข้อมูลสามส่วนทำงานคนละหน้าที่

[Training set](glossary.html#training-set) ใช้เรียนค่าภายในโมเดล [Validation set](glossary.html#validation-set) ใช้เลือกวิธีหรือค่าตั้ง เช่น จำนวนเพื่อนบ้าน $K$ ส่วน [Test set](glossary.html#test-set) เป็นข้อมูลที่กันไว้จนกว่าจะเลือกขั้นตอนทั้งหมดเสร็จ หากกลับไปปรับโมเดลจากผล test เราต้องถือว่าช่วงนั้นมีส่วนร่วมในการเลือกแล้ว

เรากำหนดการแบ่งนี้ก่อนดูคะแนนใด ๆ:

| ส่วน | วันที่ของ Features | จำนวนแถว | ใช้ทำอะไร |
|---|---|---:|---|
| Train | ม.ค. 2005–เม.ย. 2013 | 100 | fit scaler และโมเดล |
| Validation | พ.ค. 2013–ส.ค. 2016 | 40 | เลือก $K$ จากรายการที่กำหนด |
| Test | ก.ย. 2016–ธ.ค. 2019 | 40 | ประเมินขั้นตอนที่เลือกแล้ว |

คำตอบของแถวฝึกสุดท้ายรู้วันที่ 31 พฤษภาคม 2013 ซึ่งเป็นวันตัดสินใจของ validation แถวแรกพอดี เราสมมติว่าตัดสินใจหลังข้อมูลสิ้นวันเผยแพร่ครบ แล้วพยากรณ์เดือนถัดไป หากการใช้งานจริงตัดสินใจก่อนข้อมูลออก ต้องเลื่อนวันรู้ข้อมูลให้ตรงการใช้งานนั้น

```python
feature_columns = ["signal_a", "signal_b"]
train_data = validation_data.iloc[:100].copy()
tuning_data = validation_data.iloc[100:140].copy()
test_data = validation_data.iloc[140:].copy()
development_data = validation_data.iloc[:140].copy()
assert train_data["label_known_on"].max() <= tuning_data.index.min()
assert development_data["label_known_on"].max() <= test_data.index.min()
print("Rows:", len(train_data), len(tuning_data), len(test_data))
print("First validation decision:", tuning_data.index.min().date())
print("First test decision:", test_data.index.min().date())
```

`.iloc[:100]` เลือกตำแหน่ง 0 ถึง 99 โดยไม่รวมตำแหน่ง 100 ส่วน `.copy()` สร้างสำเนาเพื่อไม่ให้การแก้ตารางย่อยไปปะปนกับต้นฉบับ `assert` หยุดโปรแกรมหากเงื่อนไขไม่จริง จึงใช้ตรวจลำดับเวลาที่เราคาดไว้

การแบ่งตามเวลาเหมาะกับคำถามว่า “ฝึกจากอดีตแล้วใช้กับช่วงถัดไปได้แค่ไหน” การสุ่มสลับแถวในข้อมูลตลาดอาจนำข้อมูลภายหลังไปช่วยเรียนอดีต และทำให้แถวที่มีช่วงผลตอบแทนทับซ้อนกันกระจายอยู่ทั้งสองฝั่ง

<span id="validation-preprocessing"></span>

## การปรับสเกลก็เป็นสิ่งที่ต้องเรียนจากข้อมูลฝึก

[Data leakage](glossary.html#data-leakage) เกิดเมื่อใช้ข้อมูลที่ยังไม่มี ณ เวลาพยากรณ์ในการสร้างโมเดล มันเกิดได้ตั้งแต่ก่อนคำสั่ง `.fit` ของตัวพยากรณ์ เช่น คำนวณค่าเฉลี่ยทั้งตารางก่อนแบ่ง train/test หรือเลือก feature จากความสัมพันธ์กับคำตอบในช่วงอนาคต

ค่าเฉลี่ยที่ใช้ standardize ต้องมาจากช่วงฝึก ส่วน validation และ test ใช้ค่าเดิมในการแปลง เราคำนวณค่าเฉลี่ยสองแบบเพื่อดูว่ามันต่างกัน โดยไม่ได้ใช้ค่าเฉลี่ยทั้งตารางฝึกโมเดล

```python
training_scaler = StandardScaler().fit(train_data[feature_columns])
training_feature_mean = training_scaler.mean_.copy()
all_dates_feature_mean = validation_data[feature_columns].mean().to_numpy()
first_validation_scaled = training_scaler.transform(
    tuning_data[feature_columns].iloc[[0]]
)
print("Training means:", np.round(training_feature_mean, 6))
print("All-date means (diagnostic only):", np.round(all_dates_feature_mean, 6))
print("First validation row after scaling:", first_validation_scaled.round(4))
```

ค่าเฉลี่ยสอง features จากข้อมูลฝึกประมาณ `[0.047570, -0.066137]` ขณะที่ทั้งตารางประมาณ `[0.037305, -0.096127]` แม้ต่างกันไม่มากในตัวอย่างนี้ กระบวนการที่ใช้ข้อมูลอนาคตยังผิดหน้าที่อยู่ ขนาดของความต่างไม่ได้เป็นเกณฑ์อนุญาตให้ใช้ข้อมูลนั้น

ต่อไปเราจะใช้ `make_pipeline(StandardScaler(), KNeighborsClassifier(...))` เมื่อ fit pipeline ด้วย train ตัว scaler และ KNN จะได้รับข้อมูลฝึกชุดเดียวกัน เวลาพยากรณ์ pipeline จะใช้ scaler ที่ fit ไว้แล้ว เอกสาร [Common pitfalls ของ scikit-learn](https://scikit-learn.org/1.6/common_pitfalls.html#data-leakage) อธิบายหลักเดียวกันสำหรับ preprocessing และการเลือก features

<span id="validation-knn-selection"></span>

## เลือกจำนวนเพื่อนบ้านจาก Validation

$K$ เป็น hyperparameter คือค่าที่เรากำหนดให้กระบวนการเรียนรู้ ต่างจากค่าเฉลี่ยที่ scaler เรียนจาก train เรากำหนดรายการ `[1, 3, 5, 9, 15, 25]` และเลือกค่าที่มีสัดส่วนคำตอบผิดใน validation ต่ำที่สุด หากเสมอกันจะใช้ค่าที่อยู่ก่อนในรายการ

```python
k_grid = np.array([1, 3, 5, 9, 15, 25])
selection_rows = []
for k in k_grid:
    candidate = make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=int(k)))
    candidate.fit(train_data[feature_columns], train_data["next_positive"])
    train_error = np.mean(candidate.predict(train_data[feature_columns]) != train_data["next_positive"])
    validation_error = np.mean(candidate.predict(tuning_data[feature_columns]) != tuning_data["next_positive"])
    selection_rows.append([int(k), train_error, validation_error])
knn_selection = pd.DataFrame(selection_rows, columns=["k", "train_error", "validation_error"])
knn_train_errors = knn_selection["train_error"].to_numpy()
knn_validation_errors = knn_selection["validation_error"].to_numpy()
selected_k = int(knn_selection.loc[knn_selection["validation_error"].idxmin(), "k"])
print(knn_selection.to_string(index=False))
print("Selected K:", selected_k)
```

ผลที่ได้ในโลกจำลองนี้คือ:

| $K$ | Train error | Validation error |
|---:|---:|---:|
| 1 | 0.0% | 47.5% |
| 3 | 13.0% | 37.5% |
| 5 | 19.0% | 37.5% |
| 9 | 20.0% | 32.5% |
| 15 | 22.0% | 37.5% |
| 25 | 21.0% | 35.0% |

เมื่อ $K=1$ และไม่มีแถวคะแนนซ้ำ แต่ละแถวฝึกมีตัวเองเป็นเพื่อนบ้านที่ใกล้ที่สุด จึงทาย train ถูกทั้งหมด แต่ผิด 19 จาก 40 แถวใน validation ลักษณะนี้แสดง [overfitting](glossary.html#overfitting): ทำได้ดีมากกับข้อมูลที่ใช้ฝึก แต่ความแม่นยำไม่ตามไปยังข้อมูลใหม่

เราเลือก $K=9$ เพราะ validation ผิด 13 จาก 40 แถว ตัวอย่างนี้ไม่ได้สรุปว่า $K=9$ เหมาะกับสินทรัพย์อื่น และ error ไม่จำเป็นต้องเพิ่มหรือลดตาม $K$ แบบเรียบเสมอ ถ้าลอง features, ช่วงเวลา และโมเดลอีกหลายร้อยชุดบน validation เดิม โอกาสเลือกผู้ชนะจากความบังเอิญก็เพิ่มขึ้นด้วย

<figure class="lesson-figure">
<picture>
<source media="(max-width: 520px)" srcset="assets/charts/ml-knn-validation-mobile.svg">
<img src="assets/charts/ml-knn-validation.svg" alt="อัตราทายผิดของ KNN บน train และ validation สำหรับ K หกค่า" loading="lazy" width="720" height="560">
</picture>
<figcaption>ตัวเลขจากโค้ดและตารางด้านบน K เท่ากับ 1 จำข้อมูลฝึกได้ดี แต่ validation error สูงกว่า K เท่ากับ 9 เส้นเชื่อมใช้ช่วยอ่านค่าที่ทดลอง โดยยังไม่เปิดผลจากชุด test</figcaption>
</figure>

<span id="validation-final-test"></span>

## ตรึงวิธี แล้วเปิด Test

นโยบายที่กำหนดไว้คือ เมื่อเลือก $K$ แล้วให้ fit ใหม่ครั้งเดียวบน train รวม validation ที่รู้คำตอบครบ ณ วันเริ่ม test จากนั้นใช้ scaler และโมเดลชุดนี้ตลอด 40 เดือนทดสอบ ไม่มีการเติมคำตอบของ test กลับเข้าโมเดลระหว่างทาง นี่เป็นการประเมินแบบ fit ครั้งเดียว ซึ่งต่างจากการ retrain ทุกเดือน

Baseline จะพยากรณ์ class ที่พบมากกว่าใน development set ตลอด test การกำหนด baseline จากคำตอบ test จะทำให้มันได้ข้อมูลที่คู่แข่งไม่มี

```python
final_knn = make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=selected_k))
final_knn.fit(development_data[feature_columns], development_data["next_positive"])
test_predictions = final_knn.predict(test_data[feature_columns])
test_error = np.mean(test_predictions != test_data["next_positive"])
baseline_class = int(development_data["next_positive"].mean() >= 0.5)
test_baseline_error = np.mean(baseline_class != test_data["next_positive"])
test_error_by_half = [np.mean(test_predictions[a:b] != test_data["next_positive"].iloc[a:b])
                      for a, b in [(0, 20), (20, 40)]]
print(f"Final test error: {test_error:.1%}; baseline: {test_baseline_error:.1%}")
print("Errors in two consecutive 20-month blocks:", test_error_by_half)
```

Test error เท่ากับ 40% หรือผิด 16 จาก 40 ครั้ง ขณะที่ baseline ผิด 50% ความต่างจาก validation 32.5% เกิดได้แม้สูตรสร้างข้อมูลไม่เปลี่ยน เพราะผลของตัวอย่างใหม่และการ fit ใหม่ เรามีเพียง 40 การทดลองในช่วงสุดท้าย จึงยังไม่ควรตีความความต่าง 10 จุดเปอร์เซ็นต์จาก baseline เป็นคุณสมบัติถาวรของวิธี

คะแนนรายช่วงช่วยเห็นว่าความผิดพลาดกระจุกตัวหรือไม่ แต่หลังเปิด test แล้ว การเลือกย้อนกลับไปใช้ $K$ อื่นเพราะดูเหมือนจะชนะ test ต้องมีข้อมูลอนาคตชุดใหม่สำหรับการประเมินรอบต่อไป ถ้ารายงานการลองทั้งหมดตามจริง ช่วงเดิมยังใช้วิเคราะห์ได้ เพียงไม่ควรเรียกว่า holdout ที่ไม่เคยใช้ตัดสินใจ

<span id="validation-cross-validation"></span>

## Expanding-window Cross-validation

[Cross-validation](glossary.html#cross-validation) ประเมินกระบวนการเรียนรู้บนหลายรอบการแบ่งข้อมูล สำหรับอนุกรมเวลา เราให้ช่วงฝึกมาก่อนช่วงประเมินในแต่ละรอบ และขยายช่วงฝึกไปข้างหน้า

ตัวอย่างนี้สาธิต `TimeSeriesSplit` เฉพาะ 140 แถว development โดยใช้ $K=9$ ที่เลือกไว้แล้ว ไม่ใช้คะแนนรอบนี้ย้อนกลับไปเปลี่ยนผล test ก่อนหน้า `n_splits=3` ขอสามรอบ `test_size=20` กำหนดช่วงประเมินรอบละ 20 แถว และ `gap=1` เว้นหนึ่งแถวระหว่างฝึกกับประเมิน ในรอบเหล่านี้คำว่า test ของ API ทำหน้าที่เป็น validation ภายใน development set

```python
from sklearn.model_selection import TimeSeriesSplit

time_splitter = TimeSeriesSplit(n_splits=3, test_size=20, gap=1)
cv_rows = []
for fold, (fit_positions, check_positions) in enumerate(time_splitter.split(development_data), 1):
    fold_train = development_data.iloc[fit_positions]
    fold_check = development_data.iloc[check_positions]
    assert fold_train["label_known_on"].max() <= fold_check.index.min()
    fold_model = make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=selected_k))
    fold_model.fit(fold_train[feature_columns], fold_train["next_positive"])
    fold_error = np.mean(fold_model.predict(fold_check[feature_columns]) != fold_check["next_positive"])
    cv_rows.append([fold, len(fold_train), fit_positions[-1], check_positions[0], fold_error])
time_cv_results = pd.DataFrame(cv_rows, columns=["fold", "n_train", "last_train", "first_check", "error"])
print(time_cv_results.to_string(index=False))
```

จำนวนแถวฝึกคือ 79, 99 และ 119; ตำแหน่งฝึกสุดท้ายคือ 78, 98 และ 118 ขณะที่ช่วงประเมินเริ่มตำแหน่ง 80, 100 และ 120 ตามลำดับ Error แต่ละรอบเป็น 35%, 30% และ 40% การ fit pipeline ใหม่ในแต่ละรอบทำให้ค่าเฉลี่ยและ SD ของ scaler มาจากช่วงฝึกของรอบนั้นเท่านั้น

การเว้นหนึ่งแถวเป็น buffer เพิ่มเติมสำหรับตัวอย่างเป้าหมายหนึ่งเดือนนี้ ไม่ใช่สูตรตายตัวสำหรับทุกข้อมูล หากเป้าหมายเป็นผลตอบแทนสามเดือนข้างหน้า ต้องตรวจวันสิ้นสุดของเป้าหมายแต่ละแถว และตัดแถวที่ยังไม่รู้คำตอบออก อาจต้องจัดการการทับซ้อนของช่วงเป้าหมายเพิ่มเติมด้วย เอกสาร [TimeSeriesSplit](https://scikit-learn.org/1.6/modules/generated/sklearn.model_selection.TimeSeriesSplit.html) ระบุว่า `gap` นับจำนวนแถว และไม่ได้อ่านความหมายของ target ให้เรา

<span id="validation-label-horizon"></span>

## ขอบเขตเวลาเปลี่ยนเมื่อ Target ยาวขึ้น

ลองใช้วันที่เดิมแต่สมมติว่า target รู้ช้าสามเดือน ตัดสินใจครั้งแรกที่ 31 พฤษภาคม 2013 แถวที่ใช้ฝึกได้ล่าสุดจะเลื่อนจากเมษายนกลับไปเป็นกุมภาพันธ์ แม้ features ของมีนาคมกับเมษายนมีอยู่แล้วก็ตาม

```python
timing_cutoff = tuning_data.index[0]
one_month_known = validation_data["label_known_on"] <= timing_cutoff
three_month_known_on = validation_data.index + pd.offsets.MonthEnd(3)
three_month_known = three_month_known_on <= timing_cutoff
print("One-month latest feature date:", validation_data.index[one_month_known].max().date())
print("Three-month latest feature date:", validation_data.index[three_month_known].max().date())
print("Eligible rows:", int(one_month_known.sum()), int(three_month_known.sum()))
```

ผลคือวันที่ 30 เมษายนกับ 28 กุมภาพันธ์ 2013 และจำนวนแถว 100 กับ 98 โค้ดนี้ตรวจปฏิทินการรู้คำตอบเท่านั้น ไม่ได้เปลี่ยน target 0/1 เดิมให้กลายเป็นผลตอบแทนสามเดือน หากจะเปลี่ยนโจทย์จริงต้องสร้างคำตอบใหม่ให้ตรง horizon ด้วย

ข้อมูลเศรษฐกิจยังมีวันประกาศและการปรับปรุงย้อนหลัง เช่น ค่าของเดือนมีนาคมอาจเผยแพร่กลางเมษายน การใส่แถวไว้ที่วันที่ 31 มีนาคมไม่ได้ทำให้เรารู้ค่านั้นในเดือนมีนาคม ต้องเก็บเวลาประกาศหรือข้อมูลรุ่นที่มีอยู่จริง ณ วันตัดสินใจ

<span id="validation-future-perturbation"></span>

## ตรวจว่าแก้อนาคตแล้วคำพยากรณ์อดีตยังเหมือนเดิม

เราสามารถทดสอบขอบเขตข้อมูลของโปรแกรมได้โดยเปลี่ยนข้อมูลที่ยังไม่ทราบ ณ วันตัดสินใจ แล้วตรวจว่าคำพยากรณ์วันนั้นไม่เปลี่ยน ฟังก์ชันต่อไปนี้ fit KNN ใหม่จากแถวที่วันรู้คำตอบไม่เกิน `decision_date` และใช้ features ของวันตัดสินใจเป็นคำถามใหม่

ในส่วนนี้ใช้ $K=5$ ที่กำหนดคงที่เพื่อทดสอบเวลาโดยเฉพาะ จึงไม่มีการเลือก $K$ ด้วยข้อมูลที่มาภายหลังแต่แฝงอยู่ในฟังก์ชัน ผลทดสอบนี้ไม่ใช่การประเมินคะแนนอีกวิธีเพื่อเลือกแทน $K=9$

```python
def fit_predict_at(data, decision_date, k=5):
    decision_date = pd.Timestamp(decision_date)
    eligible = (data.index < decision_date) & (data["label_known_on"] <= decision_date)
    available = data.loc[eligible]
    model = make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=k))
    model.fit(available[feature_columns], available["next_positive"])
    probability = model.predict_proba(data.loc[[decision_date], feature_columns])[0, 1]
    return {"probability": probability, "model": model, "train_dates": available.index.copy()}

audit_cutoff = validation_dates[120]
original_audit = fit_predict_at(validation_data, audit_cutoff)
print("Decision date:", audit_cutoff.date())
print("Training rows:", len(original_audit["train_dates"]))
print("Probability:", original_audit["probability"])
```

`&` เชื่อมเงื่อนไขรายแถวโดยต้องใส่วงเล็บให้แต่ละเงื่อนไข ฟังก์ชันคืน dictionary ซึ่งเก็บทั้งคำพยากรณ์ ตัวโมเดล และวันที่ใช้ฝึก เราจึงตรวจได้มากกว่าแค่ดูว่าคำตอบ 0/1 บังเอิญตรงกันหรือไม่

ต่อไปเปลี่ยน features ที่มีวันที่หลัง cutoff อย่างมาก และสลับคำตอบทุกแถวที่รู้หลัง cutoff สังเกตว่ารวมถึงคำตอบของแถว cutoff เอง เพราะผลเดือนถัดไปยังไม่เกิด ณ ตอนตัดสินใจ

```python
def perturb_future(data, cutoff):
    altered = data.copy(deep=True)
    future_features = altered.index > pd.Timestamp(cutoff)
    future_labels = altered["label_known_on"] > pd.Timestamp(cutoff)
    altered.loc[future_features, feature_columns] = 100 + 7 * altered.loc[future_features, feature_columns]
    altered.loc[future_labels, "next_positive"] = 1 - altered.loc[future_labels, "next_positive"]
    return altered

perturbed_data = perturb_future(validation_data, audit_cutoff)
altered_audit = fit_predict_at(perturbed_data, audit_cutoff)
audit_dates = validation_dates[115:121]
original_probabilities = np.array([fit_predict_at(validation_data, d)["probability"] for d in audit_dates])
perturbed_probabilities = np.array([fit_predict_at(perturbed_data, d)["probability"] for d in audit_dates])
assert np.array_equal(original_probabilities, perturbed_probabilities)
assert original_audit["train_dates"].equals(altered_audit["train_dates"])
assert np.allclose(original_audit["model"][0].mean_, altered_audit["model"][0].mean_)
print("Probabilities unchanged:", original_probabilities)
```

ทั้งหกคำพยากรณ์และค่าเฉลี่ยของ scaler ที่ตรวจคงเดิม การทดสอบนี้จะช่วยจับโค้ดที่เผลอ fit scaler จากทั้งตารางหรือใช้คำตอบที่ยังไม่ประกาศ อย่างไรก็ตาม มันตรวจได้เท่าที่เราแก้ข้อมูลและเท่าที่ timestamps ถูกต้อง หาก feature ต้นทางคำนวณด้วยราคาวันพรุ่งนี้แต่ติดป้ายวันนี้ตั้งแต่ก่อนเข้าฟังก์ชัน โปรแกรมนี้ตรวจไม่พบ ต้องตรวจวิธีสร้าง features ด้วย

<span id="validation-ensembles"></span>

## Ensemble ช่วยได้เมื่อความผิดพลาดไม่เหมือนกันทั้งหมด

[Ensemble learning](glossary.html#ensemble-learning) รวมคำพยากรณ์ของหลายโมเดล เช่น เฉลี่ยตัวเลขหรือความน่าจะเป็น และใช้เสียงส่วนใหญ่กับ class สำหรับ regression ให้ errors ของสองโมเดลเป็น $e_A,e_B$ เมื่อเฉลี่ยเท่ากัน error จะเป็น $(e_A+e_B)/2$ ดังนั้น

$$
E[e_{\mathrm{avg}}^2]
=\tfrac14\left(E[e_A^2]+E[e_B^2]+2E[e_Ae_B]\right).
$$

ถ้าผิดคนละทิศบางครั้ง พจน์ผลคูณอาจช่วยลด MSE ของค่าเฉลี่ย แต่ถ้าทั้งคู่ผิดเหมือนกัน การเฉลี่ยก็ไม่ทำให้ความผิดนั้นหายไป ลองข้อมูลผลตอบแทนสี่ช่วงที่สร้างแยกจากโจทย์ classification:

```python
ensemble_truth = np.array([0.01, -0.02, 0.03, 0.00])
forecast_a = ensemble_truth + np.array([0.01, -0.01, 0.01, -0.01])
forecast_b = ensemble_truth + np.array([-0.01, 0.01, 0.01, -0.01])
forecast_average = (forecast_a + forecast_b) / 2
ensemble_mse = pd.Series({
    "A": np.mean((forecast_a - ensemble_truth) ** 2),
    "B": np.mean((forecast_b - ensemble_truth) ** 2),
    "Average": np.mean((forecast_average - ensemble_truth) ** 2),
    "A averaged with itself": np.mean(((forecast_a + forecast_a) / 2 - ensemble_truth) ** 2),
})
print(ensemble_mse)
```

A และ B มี MSE เท่ากันที่ 0.0001 ส่วนค่าเฉลี่ยมี MSE 0.00005 เพราะ errors ของสองช่วงแรกหักล้างกัน อีกสองช่วงยังเท่าเดิม หากเฉลี่ย A กับตัวเอง MSE ก็ยัง 0.0001 ตัวเลขเหล่านี้เป็นผลกำลังสองของผลตอบแทนทศนิยม การรวมโมเดลที่แย่มากอาจทำให้ผลแย่ลงได้

การเฉลี่ยหรือ voting นี้ต่างจาก boosting ซึ่งสร้างผู้เรียนต่อเนื่องตามกฎของ algorithm เพื่อปรับปรุงสิ่งที่ชุดก่อนทำได้ไม่ดี ส่วน bagging ฝึกหลายโมเดลบนตัวอย่างที่สุ่มจากชุดฝึก แนวคิดทั้งหมดต้องประเมินตามเวลาเช่นเดียวกับโมเดลเดี่ยว น้ำหนัก ensemble ที่เรียนจากคำตอบ test ก็ทำให้ test มีส่วนร่วมในการฝึก

<span id="validation-shrinkage"></span>

## Shrinkage ยอมให้ Fit ไม่แน่นเท่าเดิม

อีกทางลดความไวต่อรายละเอียดของตัวอย่างคือจำกัดขนาดสัมประสิทธิ์ ลอง regression ตัวแปรเดียวที่จัดให้ $x$ และ $y$ มีค่าเฉลี่ยศูนย์แล้ว Ridge ใน convention ของตัวอย่างนี้ลด

$$
\sum_i(y_i-bx_i)^2+\lambda b^2,
\qquad
b_\lambda=\frac{\sum_i x_i y_i}{\sum_i x_i^2+\lambda}.
$$

เมื่อ $\lambda>0$ ตัวหารใหญ่ขึ้น สัมประสิทธิ์จึงถูกดึงเข้าหาศูนย์ สูตรนี้ใช้ผลรวม squared error โดยไม่หารจำนวนแถว หากเปลี่ยนเป็นค่าเฉลี่ย การเทียบค่า $\lambda$ ต้องเปลี่ยนตามด้วย

```python
shrink_x = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
shrink_y = np.array([-0.015, -0.012, 0.0, 0.012, 0.015])
ridge_lambdas = np.array([0.0, 2.0, 10.0])
ridge_slopes = np.sum(shrink_x * shrink_y) / (np.sum(shrink_x ** 2) + ridge_lambdas)
ridge_training_mse = np.array([np.mean((shrink_y - b * shrink_x) ** 2) for b in ridge_slopes])
print(pd.DataFrame({"lambda": ridge_lambdas, "slope": ridge_slopes,
                    "train_mse": ridge_training_mse}))
```

สัมประสิทธิ์ลดจาก 0.0084 เป็น 0.0070 และ 0.0042 เมื่อ $\lambda$ เพิ่มจาก 0 เป็น 2 และ 10 การยอมให้ training error สูงขึ้นอาจแลกกับความไวต่อตัวอย่างที่ลดลง แต่ไม่ได้รับประกันว่าจะทายอนาคตดีขึ้น ต้องเลือกความแรงของ penalty ด้วย validation และเก็บ test ไว้ตามเดิม ดูการใช้กับหลาย factors ต่อใน[บท Regularized Factor Models](regularized-factor-models.html)

<span id="validation-exercises"></span>

## แบบฝึกหัดพร้อมวิธีคิด

### 1. วันที่อยู่ในไฟล์เพียงพอหรือไม่

ข้อมูลเศรษฐกิจประจำเดือนมกราคมประกาศวันที่ 15 กุมภาพันธ์ จะใช้ทายผลตอบแทนวันที่ 1 กุมภาพันธ์ได้หรือไม่?

ใช้ไม่ได้ เพราะ ณ วันตัดสินใจยังไม่มีตัวเลขนั้น วันที่ที่ข้อมูลอธิบายกับวันที่ผู้ลงทุนได้รับข้อมูลเป็นคนละเรื่อง ต้องเลื่อนเวลาใช้ feature ไปหลังวันประกาศ และใช้ข้อมูลรุ่นที่ประกาศจริงในวันนั้น

### 2. ทำไม KNN หนึ่งเพื่อนบ้านได้ Train error ศูนย์

สำหรับคะแนนที่ไม่ซ้ำกัน เมื่อถามด้วยแถวฝึกเดิม เพื่อนบ้านที่ใกล้ที่สุดคือตัวมันเอง ระยะทางศูนย์จึงให้ label เดิม การทายตัวเองถูกไม่ได้บอกความแม่นยำต่อแถวใหม่ หากคะแนนซ้ำแต่ labels ขัดกัน ผลนี้ก็ไม่จำเป็นต้องเกิด

### 3. เลือก K จาก Test ได้หรือไม่

สมมติ $K=9$ ชนะ validation แต่ $K=15$ ชนะ test แล้วรายงานเฉพาะ $K=15$ เป็นผลทดสอบสุดท้ายได้หรือไม่?

ต้องรายงานว่าใช้ test เลือกวิธีแล้ว และต้องมีข้อมูลใหม่หากต้องการประเมินการเลือกนี้แบบไม่เคยใช้ตัดสินใจมาก่อน การเปลี่ยนชื่อไฟล์จาก test เป็น validation ไม่ได้สร้างข้อมูลที่ยังไม่เคยเห็นขึ้นมา

### 4. Gap หนึ่งแถวพอสำหรับทุก Target หรือไม่

ไม่พอเสมอไป แถวสิ้นเดือนมีนาคมที่ทายผลตอบแทนเมษายนถึงมิถุนายนยังไม่รู้คำตอบสิ้นพฤษภาคม ต้องเช็ก `label_known_on` ของแต่ละแถวตาม horizon และวันประกาศจริง จำนวนแถวที่ต้องเว้นจึงขึ้นกับโจทย์และความถี่ข้อมูล

### 5. คำตอบใดของวัน Cutoff ต้องถือเป็นอนาคต

ในข้อมูลของบทนี้ features ของวัน cutoff มีอยู่แล้ว แต่ label ของแถวนั้นอธิบายเดือนถัดไป จึงยังใช้ฝึกไม่ได้ `perturb_future` เปลี่ยน label แถวนั้นได้โดยที่คำพยากรณ์ ณ cutoff ต้องคงเดิม

### 6. Pipeline แก้การรั่วไหลทุกชนิดหรือไม่

Pipeline ช่วยให้การแปลงข้อมูล fit บนชุดที่ส่งเข้า `.fit` แต่ถ้าเราส่งทั้งตารางเข้า `.fit` หรือสร้าง feature จากอนาคตก่อนเข้า pipeline ก็ยังรั่วได้ การตรวจวันรู้ข้อมูลและการแบ่งชุดจึงต้องทำควบคู่กัน

### 7. Ensemble สองตัวเหมือนกันช่วยเท่าไร

ถ้า forecasts สองชุดเหมือนกันทุกแถว ค่าเฉลี่ยก็เหมือนเดิมทุกแถว MSE จึงไม่ลด ในตัวอย่าง A เฉลี่ยกับ A ยังคงมี MSE 0.0001 ความหลากหลายของชื่อโมเดลไม่เพียงพอ ต้องดูความผิดพลาดจริงร่วมกันด้วย

### 8. Test error 40% แปลว่าพอร์ตมีกำไรหรือไม่

ยังตอบไม่ได้ เรานับแค่ทิศทางถูกหรือผิด ยังไม่มีขนาดกำไรและขาดทุน น้ำหนักสินทรัพย์ ความถี่ซื้อขาย หรือต้นทุน ต้องกำหนดกฎตัดสินใจและทดสอบผลตอบแทนพอร์ตสุทธิในข้อมูลที่กระบวนการสร้างกฎไม่เคยใช้มาก่อน

<span id="validation-sources"></span>

## ที่มาและขอบเขต

แนวคิดการประเมิน การรวมผู้เรียน และข้อจำกัดในงานลงทุนเรียบเรียงใหม่หลังอ่าน transcript เต็มของ [Highlights of Best Practice](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/4mqDE/highlights-of-best-practice) และ [Challenges Ahead](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/1Ba4p/challenges-ahead) เมื่อ 3 ตุลาคม 2026 ตัวอย่าง วันที่ ตัวเลข และโค้ดในหน้านี้สร้างใหม่ทั้งหมด

ตรวจพฤติกรรมซอฟต์แวร์กับเอกสาร scikit-learn 1.6 เรื่อง [Data leakage](https://scikit-learn.org/1.6/common_pitfalls.html#data-leakage), [Time-series cross-validation](https://scikit-learn.org/1.6/modules/cross_validation.html#cross-validation-of-time-series-data), [TimeSeriesSplit](https://scikit-learn.org/1.6/modules/generated/sklearn.model_selection.TimeSeriesSplit.html), [Voting ensembles](https://scikit-learn.org/1.6/modules/ensemble.html#voting-classifier) และ [Ridge regression](https://scikit-learn.org/1.6/modules/linear_model.html#ridge-regression-and-classification) บทนี้แยก train/validation/test และ boosting ออกจาก voting เพื่อให้หน้าที่ของแต่ละขั้นตอนตรงกับวิธีที่ใช้จริง

บทถัดไปจะกำหนดหน่วยผลตอบแทน คำนวณน้ำหนัก และติดตามมูลค่าเงินใน[ตัวอย่างพอร์ตที่กันช่วงทดสอบ](ml-portfolio-lab.html)
