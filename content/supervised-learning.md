---
title: "เริ่มพยากรณ์ด้วย Regression และเพื่อนบ้าน"
description: "คำนวณ Linear Regression, Logistic Regression, KNN และแนวคิด SVM จากตัวอย่างเล็ก พร้อม Loss, Confusion Matrix และการปรับสเกล Features"
---

# เริ่มพยากรณ์ด้วย Regression และเพื่อนบ้าน

<p class="lead">เมื่อแยก Feature กับ Target ได้แล้ว เราต้องเลือกวิธีแปลงข้อมูลเข้าเป็นคำพยากรณ์ เส้นตรงหนึ่งเส้นอาจพออธิบายข้อมูลบางชุด ขณะที่อีกชุดต้องอาศัยตัวอย่างใกล้เคียง บทนี้จะคำนวณคำตอบด้วยมือก่อนเรียก scikit-learn แล้วตรวจว่าแต่ละวิธีลดความผิดพลาดชนิดใด</p>

อ่าน[บทพื้นฐาน ML](ml-foundations.html)ก่อนหากยังไม่คุ้นกับ $X$, $y$ และเวลาที่รู้คำตอบ ทุกข้อมูลในหน้านี้สร้างขึ้นใหม่เพื่อฝึกคำนวณ ไม่ใช่ผลทดลองกับตลาดจริง เราแยกตัวอย่าง regression, classification และการปรับสเกลอย่างชัดเจน ไม่เปรียบเทียบคะแนนข้ามชุดข้อมูลว่าโมเดลใดดีที่สุด

โค้ดใช้ NumPy, pandas และ scikit-learn 1.6.1 รันเรียงจากต้นหน้าใน Notebook ใหม่ได้ `scikit-learn` เป็นชื่อแพ็กเกจที่ติดตั้ง ส่วนชื่อที่ใช้ในคำสั่ง `import` คือ `sklearn` โดยแต่ละโมเดลมักมี `.fit(X, y)` สำหรับเรียนจากข้อมูลและ `.predict(X_new)` สำหรับพยากรณ์ข้อมูลใหม่

<span id="supervised-regression-data"></span>

## เริ่มจาก Feature เดียวและผลตอบแทนหนึ่งช่วง

ให้ `signal_score` เป็นคะแนนสมมติที่ไม่มีหน่วย โดยสมมติว่าทราบก่อนช่วงผลตอบแทนที่ต้องการพยากรณ์ เรายังไม่กำหนดสูตรสร้างคะแนนนี้ เพราะต้องการศึกษาวิธี fit เส้นตรงก่อน ผลตอบแทนเป้าหมายเป็นรายเดือนหน่วยทศนิยม

ข้อมูลหกแถวแรกใช้ฝึกโมเดล โดยคู่ feature/target ของทั้งหกแถวทราบครบก่อนเริ่มประเมินสามแถวถัดไป ข้อมูลประเมินจะแยกไว้อีกตาราง เราไม่ใช้คำตอบสามแถวหลังในการประมาณเส้นตรง

```python
import numpy as np
import pandas as pd

regression_train = pd.DataFrame({
    "signal_score": [-2.0, -1.0, 0.0, 1.0, 2.0, 3.0],
    "next_return": [-0.009, -0.006, 0.003, 0.009, 0.012, 0.021],
})
regression_test = pd.DataFrame({
    "signal_score": [-1.5, 0.5, 2.5],
    "next_return": [-0.010, 0.007, 0.016],
})
reg_x = regression_train["signal_score"].to_numpy()
reg_y = regression_train["next_return"].to_numpy()
print(regression_train)
```

เช่น คะแนน −2 คู่กับผลตอบแทนเดือนถัดไป −0.9% ส่วนคะแนน 3 คู่กับ +2.1% เราจะประมาณความสัมพันธ์ในรูป

$$
\hat y_i=a+b x_i.
$$

$a$ คือ intercept หรือค่าพยากรณ์เมื่อคะแนนเป็นศูนย์ และ $b$ คือ slope หรือการเปลี่ยนของค่าพยากรณ์เมื่อคะแนนเพิ่มหนึ่งหน่วย คำว่า linear ในที่นี้หมายถึงรูปแบบเชิงเส้นของพารามิเตอร์ในโมเดลที่กำหนด ไม่ได้ยืนยันว่าความสัมพันธ์ของตลาดจริงต้องเป็นเส้นตรง

<span id="supervised-ols-by-hand"></span>

## Ordinary Least Squares เลือกเส้นที่ลด Squared Error

Ordinary least squares หรือ OLS เลือก $a,b$ ให้ผลรวม $(y_i-a-bx_i)^2$ ต่ำที่สุด เมื่อมี feature เดียวที่ไม่ใช่ค่าคงที่ คำตอบคือ

$$
b=\frac{\sum_i(x_i-\bar x)(y_i-\bar y)}{\sum_i(x_i-\bar x)^2},
\qquad a=\bar y-b\bar x.
$$

เศษดูว่า $x$ และ $y$ เคลื่อนไปรอบค่าเฉลี่ยในทิศเดียวกันมากเพียงใด ส่วนหารปรับตามการกระจายของ $x$ ในข้อมูลนี้ $\bar x=0.5$, $\bar y=0.005$, เศษเท่ากับ 0.105 และส่วนเท่ากับ 17.5 จึงได้ $b=0.006$ และ $a=0.002$

```python
reg_x_mean = reg_x.mean()
reg_y_mean = reg_y.mean()
ols_numerator = np.sum((reg_x - reg_x_mean) * (reg_y - reg_y_mean))
ols_denominator = np.sum((reg_x - reg_x_mean) ** 2)
ols_slope = ols_numerator / ols_denominator
ols_intercept = reg_y_mean - ols_slope * reg_x_mean
ols_train_predictions = ols_intercept + ols_slope * reg_x
ols_residuals = reg_y - ols_train_predictions
print(f"Intercept: {ols_intercept:.6f}; slope: {ols_slope:.6f}")
print("Residuals:", np.round(ols_residuals, 6))
```

เส้นที่ได้คือ $\hat y=0.002+0.006x$ คะแนนเพิ่มหนึ่งหน่วยทำให้ผลตอบแทนที่พยากรณ์เพิ่ม 0.6 จุดเปอร์เซ็นต์ต่อเดือน และเมื่อคะแนนศูนย์จะพยากรณ์ 0.2% ต่อเดือน Residual ตามนิยามค่าจริงลบค่าพยากรณ์คือ `[0.001, -0.002, 0.001, 0.001, -0.002, 0.001]`

เราใช้ residual กับ error แบบกลับเครื่องหมายจากบทก่อน แต่ squared error เท่ากัน เพราะ $e^2=(-e)^2$ การคำนวณ OLS ไม่ต้องสมมติว่า errors เป็น Normal เพื่อหาจุดที่ลดผลรวมกำลังสอง ส่วนการสร้างช่วงความเชื่อมั่นและการตีความเชิงสถิติต้องมีสมมติฐานเพิ่มเติม ความสัมพันธ์ที่ fit ได้ยังไม่ใช่ข้อพิสูจน์ว่า feature ทำให้ผลตอบแทนเปลี่ยน

<span id="supervised-fit-predict"></span>

## ตรวจคำตอบเดียวกันด้วย scikit-learn

`LinearRegression()` สร้างตัวโมเดลที่ยังไม่ฝึก `.fit(...)` ประมาณพารามิเตอร์จากข้อมูลฝึก แล้ว `.coef_` และ `.intercept_` เก็บค่าที่เรียนได้ เครื่องหมาย `_` ท้ายชื่อเป็นรูปแบบที่ scikit-learn ใช้กับผลที่เกิดจากการ fit

Features ต้องมีสองมิติคือ `(จำนวนแถว, จำนวน features)` แม้มี feature เดียว การใช้ `[["signal_score"]]` จึงคืนตารางหนึ่งคอลัมน์ ส่วน target ใช้ Series หนึ่งมิติได้ `np.allclose` ตรวจว่าเลขที่คำนวณสองทางตรงกันภายในความละเอียดทศนิยม

```python
from sklearn.linear_model import LinearRegression

linear_model = LinearRegression()
linear_model.fit(regression_train[["signal_score"]], regression_train["next_return"])
ols_test_predictions = linear_model.predict(regression_test[["signal_score"]])
print("Library intercept and slope:", linear_model.intercept_, linear_model.coef_)
print("Matches hand calculation:", np.allclose(
    [linear_model.intercept_, linear_model.coef_[0]], [ols_intercept, ols_slope]
))
print("Predicted test returns (%):", np.round(100 * ols_test_predictions, 2))
```

ได้คำตอบตรงกับสูตรมือ และค่าพยากรณ์สามแถวหลังคือ `[-0.7, 0.5, 1.7]`% เทียบกับคำตอบจริง `[-1.0, 0.7, 1.6]`% คำสั่ง `.predict` ใช้พารามิเตอร์เดิมกับ features ใหม่ ไม่ได้ฝึกใหม่หรือใช้ target ในตารางประเมิน

<span id="supervised-baseline"></span>

## เทียบกับ Baseline ที่ไม่ใช้ Feature

Baseline คือวิธีง่ายที่ใช้เป็นจุดเปรียบเทียบ สำหรับ regression เราลองพยากรณ์ทุกแถวด้วยค่าเฉลี่ย target จากข้อมูลฝึก ซึ่งเท่ากับ 0.5% ต่อเดือน ถ้าโมเดลซับซ้อนขึ้นแต่ยังไม่ดีกว่าวิธีนี้บนข้อมูลประเมิน ก็ยังไม่มีหลักฐานจากชุดนั้นว่าการเพิ่ม feature ช่วย

```python
reg_test_target = regression_test["next_return"].to_numpy()
baseline_predictions = np.full(len(reg_test_target), reg_y_mean)
ols_test_mse = np.mean((ols_test_predictions - reg_test_target) ** 2)
baseline_test_mse = np.mean((baseline_predictions - reg_test_target) ** 2)
print(f"Linear-model test RMSE: {np.sqrt(ols_test_mse):.4%}")
print(f"Mean-baseline test RMSE: {np.sqrt(baseline_test_mse):.4%}")
print(f"Linear-model train RMSE: {np.sqrt(np.mean(ols_residuals ** 2)):.4%}")
```

RMSE บนข้อมูลประเมินเท่ากับ 0.2160 จุดเปอร์เซ็นต์สำหรับเส้นตรง และ 1.0801 จุดเปอร์เซ็นต์สำหรับ baseline ส่วน training RMSE ของเส้นตรงคือ 0.1414 จุดเปอร์เซ็นต์ ตัวเลขนี้เป็นผลของข้อมูลสมมติชุดเล็กที่เราออกแบบให้มีความสัมพันธ์ ไม่ใช่หลักฐานว่าใช้คะแนนนี้ทายหุ้นจริงได้

การเลือกโมเดลหลายครั้งแล้วรายงานเฉพาะวิธีที่ได้ test RMSE ต่ำที่สุดจะเปลี่ยนชุดทดสอบให้กลายเป็นข้อมูลที่ใช้เลือกโมเดล เราจะจัดหน้าที่ของ train, validation และ test แยกกันใน[บทถัดไป](model-validation.html)

<span id="supervised-logistic-loss"></span>

## Logistic Regression พยากรณ์ความน่าจะเป็น

เปลี่ยนโจทย์เป็น class 1 เมื่อผลตอบแทนเดือนถัดไปบวก และ class 0 เมื่อไม่บวก Logistic regression สร้างคะแนนเชิงเส้น $z=a+bx$ แล้วแปลงผ่าน sigmoid:

$$
p=\frac{1}{1+e^{-z}}.
$$

เมื่อ $z=0$ จะได้ $p=0.5$ และเมื่อ $z$ เพิ่ม $p$ จะเข้าใกล้หนึ่ง โดยยังอยู่ระหว่างศูนย์กับหนึ่ง อัตราส่วน $p/(1-p)$ เรียกว่า odds และ $\log[p/(1-p)]=z$ เรียกว่า log-odds สัมประสิทธิ์ $b$ จึงบอกว่าเมื่อคะแนนเพิ่มหนึ่งหน่วย log-odds ของ class 1 เปลี่ยนเท่าไร ต่างจากหน่วยจุดเปอร์เซ็นต์ของผลตอบแทนในเส้นตรงก่อนหน้า

สำหรับคำตอบ $y\in\{0,1\}$ เราวัดความผิดพลาดแบบความน่าจะเป็นด้วย [log loss](glossary.html#log-loss):

$$
\ell(y,p)=-\left[y\log p+(1-y)\log(1-p)\right].
$$

ถ้า $y=1$ จะเหลือ $-\log p$ การให้โอกาส class ที่เกิดจริงต่ำมากจึงมี loss สูง ถ้า $y=0$ จะเหลือ $-\log(1-p)$ ตัว `np.log` เป็น natural logarithm และ `np.exp` คือยกกำลังฐาน $e$

```python
example_logits = np.array([-1.0, 0.0, 1.0])
sigmoid_examples = 1 / (1 + np.exp(-example_logits))
loss_labels = np.array([1, 0])
good_probabilities = np.array([0.8, 0.2])
bad_probabilities = np.array([0.2, 0.8])

def binary_log_loss(labels, probabilities):
    p = np.clip(probabilities, 1e-15, 1 - 1e-15)
    return -np.mean(labels * np.log(p) + (1 - labels) * np.log(1 - p))

print("Sigmoid:", np.round(sigmoid_examples, 6))
print("Good / bad probability loss:",
      binary_log_loss(loss_labels, good_probabilities),
      binary_log_loss(loss_labels, bad_probabilities))
```

Sigmoid ได้ประมาณ `[0.268941, 0.5, 0.731059]` คู่ความน่าจะเป็นที่ให้โอกาสคำตอบถูก 80% มี log loss 0.223144 ส่วนคู่ที่ให้โอกาสคำตอบถูกเพียง 20% มี loss 1.609438 ฟังก์ชันใช้ `np.clip` ป้องกันการคำนวณ `log(0)` ที่ขอบจากการเก็บเลขทศนิยม โดยตัวอย่างทั้งหมดอยู่ภายในช่วงและไม่ได้ถูกเปลี่ยนค่า

Logistic regression มาตรฐานใช้ log loss ร่วมกับ penalty หากกำหนดไว้ ไม่ได้ลดระยะทางกำลังสองจากจุดถึงเส้นแบ่งประเภทแบบ OLS รายละเอียด objective อยู่ใน [scikit-learn: Logistic regression](https://scikit-learn.org/1.6/modules/linear_model.html#logistic-regression)

<span id="supervised-logistic-fit"></span>

## ฝึกโมเดลความน่าจะเป็นกับตัวอย่างที่มี Label

ข้อมูลชุดใหม่มีคะแนนสิบค่าและ class ของผลตอบแทนช่วงถัดไปที่สมมติขึ้น เราใส่ทั้งกรณีคะแนนติดลบแต่ผลตอบแทนบวก และคะแนนบวกแต่ผลตอบแทนไม่บวก เพื่อให้การแยกประเภทไม่ได้สมบูรณ์ด้วยเส้นเดียว

`reshape(-1, 1)` จัด array หนึ่งมิติเป็นหนึ่งคอลัมน์ โดย `-1` ให้ NumPy นับจำนวนแถวเอง โมเดลนี้ใช้ค่าเริ่มต้นเป็น L2 penalty ซึ่งเพิ่มโทษจากสัมประสิทธิ์ยกกำลังสองเพื่อจำกัดขนาดของมัน `C=1.0` กำหนดความแรงแบบผกผัน ค่า C มากทำให้ penalty มีน้ำหนักน้อยลง ส่วน `solver="lbfgs"` เลือกวิธีเชิงตัวเลขที่ใช้ fit โดย `tol` เป็นเกณฑ์ความละเอียดสำหรับหยุดและ `max_iter` จำกัดจำนวนรอบ

```python
from sklearn.linear_model import LogisticRegression

class_x = np.array([-3.0, -2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0, 3.0, 4.0])
class_y = np.array([0, 0, 1, 0, 0, 1, 0, 1, 1, 1])
logistic_model = LogisticRegression(C=1.0, solver="lbfgs", tol=1e-10, max_iter=1000)
logistic_model.fit(class_x.reshape(-1, 1), class_y)
class_test_x = np.array([-2.5, -1.5, -0.25, 0.75, 1.5, 2.5])
class_test_y = np.array([0, 0, 0, 0, 1, 1])
class_probabilities = logistic_model.predict_proba(class_test_x.reshape(-1, 1))[:, 1]
print("Intercept / coefficient:", logistic_model.intercept_, logistic_model.coef_)
print("Positive-class probabilities:", np.round(class_probabilities, 6))
```

Intercept ประมาณ −0.261621 และ coefficient ประมาณ 0.727111 `predict_proba` คืนหนึ่งคอลัมน์ต่อ class ตามลำดับใน `classes_` สำหรับโมเดลนี้คือ `[0,1]` เราเลือกคอลัมน์ที่ตำแหน่ง 1 จึงได้โอกาสของ class 1 ประมาณ `[0.111115, 0.205497, 0.390931, 0.570456, 0.696153, 0.825801]`

Features และ labels หกแถวทดสอบแยกจากข้อมูลฝึก ทั้งหมดเป็นตัวอย่างสำหรับอ่านผลของโมเดล ชุดเล็กนี้ยังใช้ตรวจความแม่นยำระยะยาวหรือ calibration ไม่ได้ และสัมประสิทธิ์ที่เป็นบวกแสดงความสัมพันธ์ที่โมเดลเรียนจากข้อมูลชุดนี้ ไม่ใช่ข้อสรุปเชิงเหตุและผล

<span id="supervised-confusion"></span>

## Confusion Matrix บอกว่าพลาดแบบใด

ใช้เกณฑ์ $p\geq0.5$ ให้ทาย class 1 แล้วนับจำนวนคำตอบด้วย [confusion matrix](glossary.html#confusion-matrix) ตารางที่ใช้ใน scikit-learn เรียงแถวตาม class จริงและคอลัมน์ตาม class ที่ทาย เมื่อกำหนด `labels=[0,1]` จะได้

$$
\begin{bmatrix}
TN&FP\\FN&TP
\end{bmatrix}.
$$

TP คือทายบวกและจริงบวก, TN คือทายไม่บวกและจริงไม่บวก, FP คือทายบวกแต่จริงไม่บวก และ FN คือพลาดผลตอบแทนบวกเพราะทายไม่บวก นิยาม “positive” ในที่นี้ผูกกับ class 1 ตามที่เรากำหนด

```python
from sklearn.metrics import confusion_matrix

classes_at_half = (class_probabilities >= 0.5).astype(int)
class_confusion = confusion_matrix(class_test_y, classes_at_half, labels=[0, 1])
tn, fp, fn, tp = class_confusion.ravel()
class_accuracy = (tp + tn) / class_confusion.sum()
class_precision = tp / (tp + fp)
class_recall = tp / (tp + fn)
print(class_confusion)
print(f"Accuracy: {class_accuracy:.4f}; precision: {class_precision:.4f}; recall: {class_recall:.4f}")
```

ได้ตาราง `[[3,1],[0,2]]` จึงตอบถูกห้าจากหกครั้งหรือ accuracy 83.33% Precision $=TP/(TP+FP)=2/3$ บอกว่าในสามครั้งที่ทายบวก มีจริงบวกสองครั้ง ส่วน recall $=TP/(TP+FN)=2/2=1$ บอกว่าพบเดือนบวกครบทั้งสองเดือน

`.ravel()` คลี่ตารางเป็น array ตามแถว จึงจับคู่ `tn, fp, fn, tp` ได้ตามลำดับนี้ ในข้อมูลอื่นตัวหารของ precision หรือ recall อาจเป็นศูนย์ ต้องกำหนดวิธีรายงานกรณีที่ไม่มีการทายบวกหรือไม่มี class บวกจริง แทนการใช้สูตรหารโดยไม่ตรวจ

เกณฑ์ที่เหมาะขึ้นกับความเสียหายของ FP และ FN ในการตัดสินใจจริง การมี recall สูงไม่รับประกันกำไร เพราะตารางนี้ยังไม่ได้ใส่ขนาดผลตอบแทนหรือต้นทุน

<span id="supervised-threshold"></span>

## เปลี่ยน Threshold เปลี่ยนการตัดสินใจ แต่ไม่เปลี่ยนโมเดลที่ Fit แล้ว

ลองใช้ threshold 0.8 ซึ่งต้องการค่าความน่าจะเป็นสูงกว่าจึงจะทายบวก เราไม่ได้เรียก `.fit` ใหม่และไม่ได้เปลี่ยนพารามิเตอร์ ค่าความน่าจะเป็นทั้งหกจึงเหมือนเดิม แต่จำนวน FP/FN เปลี่ยนได้

```python
from sklearn.metrics import log_loss

classes_at_eight = (class_probabilities >= 0.8).astype(int)
confusion_at_eight = confusion_matrix(class_test_y, classes_at_eight, labels=[0, 1])
model_log_loss = log_loss(class_test_y, class_probabilities, labels=[0, 1])
always_zero_accuracy = np.mean(class_test_y == 0)
print("Threshold 0.8 classes:", classes_at_eight)
print(confusion_at_eight)
print(f"Probability log loss: {model_log_loss:.6f}")
print(f"Always-zero accuracy: {always_zero_accuracy:.4f}")
```

ได้ `[0,0,0,0,0,1]` และ confusion matrix `[[4,0],[1,1]]` ครั้งนี้ไม่มี FP แต่พลาดเดือนบวกหนึ่งเดือน Precision จึงเป็น 1 และ recall เป็น 0.5 ทั้ง threshold 0.5 และ 0.8 ตอบถูกห้าจากหกครั้งเท่ากัน แต่พลาดคนละแบบ

Log loss ของ probability เดิมประมาณ 0.373712 และไม่เปลี่ยนตาม threshold ที่ใช้ตัดสิน class ส่วน baseline ทายศูนย์ตลอดมี accuracy $4/6=66.67$% เพราะชุดประเมินมี class 0 มากกว่า หากต้องการเลือก threshold จากคะแนน ต้องใช้ validation ที่เตรียมไว้ การลอง threshold บน test แล้วเลือกค่าที่ดูดีที่สุดจะทำให้ test ไม่เป็นการประเมินที่กันไว้สุดท้ายอีกต่อไป

<span id="supervised-knn-hand"></span>

## KNN ให้ตัวอย่างใกล้เคียงช่วยตอบ

[K-nearest neighbors หรือ KNN](glossary.html#knn) ไม่ได้ fit เส้นตรงหนึ่งเส้นแบบ OLS แต่เก็บข้อมูลฝึกไว้ แล้วหา $K$ ตัวอย่างที่อยู่ใกล้จุดใหม่ตามระยะทางที่เลือก สำหรับ classification แบบถ่วงเท่ากัน จะทายจากเสียงส่วนมากของ labels ในเพื่อนบ้านเหล่านั้น

เริ่มด้วย feature หนึ่งมิติ ระยะทางระหว่างคะแนน $x$ กับคะแนนใหม่ $q$ คือ $|x-q|$ ถ้าคะแนนใหม่เป็น 1.2 เพื่อนบ้านที่มีคะแนน 1, 2 และ 0 อยู่ห่าง 0.2, 0.8 และ 1.2 ตามลำดับ สมมติ labels ของทั้งสามเป็น 0, 1 และ 1 จะได้ class 1 จากเสียงสองในสาม

```python
neighbor_x = np.arange(-3.0, 5.0)
neighbor_y = np.array([0, 0, 0, 1, 0, 1, 1, 1])
neighbor_query = 1.2
neighbor_distances = np.abs(neighbor_x - neighbor_query)
nearest_three = np.argsort(neighbor_distances)[:3]
neighbor_probability = neighbor_y[nearest_three].mean()
print("Nearest feature values:", neighbor_x[nearest_three])
print("Their labels:", neighbor_y[nearest_three])
print(f"Fraction labelled one: {neighbor_probability:.6f}")
```

`np.arange(-3.0, 5.0)` สร้างค่าตั้งแต่ −3 ถึง 4 โดยไม่รวมปลาย 5 `np.argsort` คืนตำแหน่งที่จะเรียงระยะทางจากน้อยไปมาก และ `[:3]` เลือกสามตำแหน่งแรก สัดส่วน label 1 เท่ากับ $2/3$ เป็น probability estimate แบบเพื่อนบ้านในตัวอย่างนี้ ไม่ได้แปลว่าความน่าจะเป็นแท้จริงของตลาดเท่ากับสองในสาม

หากใช้ $K=1$ เพื่อนบ้านที่ใกล้ที่สุดมี label 0 จึงตอบอีกแบบ ค่า K เป็น hyperparameter ที่ผู้ใช้ต้องเลือกด้วยข้อมูล validation ถ้าเล็กมากผลอาจไวต่อจุดผิดปกติ ถ้าใหญ่มากลักษณะเฉพาะบริเวณอาจถูกเฉลี่ยหาย ไม่มีค่าเดียวที่เหมาะกับทุกข้อมูล

<span id="supervised-knn-api"></span>

## ตรวจ KNN ด้วยไลบรารี

`n_neighbors=3` กำหนด K, `weights="uniform"` ให้เพื่อนบ้านแต่ละตัวมีเสียงเท่ากัน และ `metric="euclidean"` ใช้ระยะทางเส้นตรง ในหนึ่งมิติระยะทางนี้ตรงกับค่าสัมบูรณ์ที่คำนวณด้วยมือ

```python
from sklearn.neighbors import KNeighborsClassifier

knn_three = KNeighborsClassifier(n_neighbors=3, weights="uniform", metric="euclidean")
knn_three.fit(neighbor_x.reshape(-1, 1), neighbor_y)
knn_query_class = knn_three.predict([[neighbor_query]])
knn_query_probability = knn_three.predict_proba([[neighbor_query]])[0, 1]
knn_query_distances, knn_query_indices = knn_three.kneighbors([[neighbor_query]])
print("Class / probability:", knn_query_class, knn_query_probability)
print("Distances:", np.round(knn_query_distances, 3))
print("Matches hand result:", np.isclose(knn_query_probability, neighbor_probability))
```

ได้ class 1, probability $2/3$ และระยะทาง `[0.2,0.8,1.2]` ตรงกับสูตรมือ ถ้าเพื่อนบ้านที่ขอบ K มีระยะทางเสมอกันแต่ labels ต่างกัน ผลอาจขึ้นกับลำดับข้อมูลตามรายละเอียด implementation ตัวอย่างนี้เลือก query ที่ไม่เกิดการเสมอนั้น ดู [เอกสาร Nearest Neighbors](https://scikit-learn.org/1.6/modules/neighbors.html#nearest-neighbors-classification)

KNN สำหรับ regression ใช้หลักใกล้เคียงกัน แต่เฉลี่ย target ตัวเลขของเพื่อนบ้านแทนการนับ class ส่วนการมีคำว่า nonparametric ไม่ได้หมายความว่าไม่มีการตั้งค่า: เรายังเลือก K, วิธีถ่วงระยะทาง, features และสเกล

<span id="supervised-scaling"></span>

## หน่วยที่ใหญ่กว่าสามารถครอบงำระยะทาง

ใช้ตัวอย่างใหม่สามจุดที่มีสอง features คือคะแนนไม่มีหน่วยกับปริมาณซื้อขายสมมติหน่วยล้านบาท จุดใหม่มีค่า `[1.9,110]` ถ้าวัดระยะทางจากเลขดิบ ความต่างของปริมาณซื้อขาย 50 หรือ 100 จะมีน้ำหนักมากกว่าความต่างของคะแนนไม่ถึงหนึ่ง แม้เราไม่ได้ตั้งใจให้ปริมาณซื้อขายสำคัญกว่า

[Standardization](glossary.html#standardization) วิธีหนึ่งคือแปลงแต่ละคอลัมน์เป็น $z_j=(x_j-\bar x_j)/s_j$ โดยค่าเฉลี่ยและ SD ต้องคำนวณจากข้อมูลฝึกเท่านั้น จากนั้นใช้ค่าเดิมแปลงข้อมูลใหม่ ในตัวอย่างนี้ใช้ SD ตัวหาร $n$ ให้ตรงกับ `StandardScaler`

```python
scale_train = np.array([[1.0, 10.0], [1.0, 110.0], [2.0, 60.0]])
scale_labels = np.array([0, 0, 1])
scale_query = np.array([[1.9, 110.0]])
scale_mean = scale_train.mean(axis=0)
scale_sd = scale_train.std(axis=0, ddof=0)
raw_distances = np.sqrt(np.sum((scale_train - scale_query) ** 2, axis=1))
scaled_train = (scale_train - scale_mean) / scale_sd
scaled_query = (scale_query - scale_mean) / scale_sd
scaled_distances = np.sqrt(np.sum((scaled_train - scaled_query) ** 2, axis=1))
print("Training means / SD:", scale_mean, scale_sd)
print("Raw distances:", np.round(raw_distances, 4))
print("Standardized distances:", np.round(scaled_distances, 4))
```

ค่าเฉลี่ยคอลัมน์คือ `[1.333333,60]` และ SD ประมาณ `[0.471405,40.824829]` ระยะทางดิบประมาณ `[100.0040,0.9,50.0001]` จึงเลือกจุดที่สองซึ่ง label 0 แต่ระยะทางหลัง standardize ประมาณ `[3.1056,1.9092,1.2430]` จึงเลือกจุดที่สามซึ่ง label 1

การปรับสเกลเปลี่ยนความหมายของความใกล้ เราต้องเลือกให้ตรงกับงาน ไม่ควรสรุปว่าคำตอบหลัง standardize ถูกกว่าโดยยังไม่มีข้อมูลประเมิน สำหรับคอลัมน์ที่ค่าคงที่ทุกแถว SD เป็นศูนย์และใช้สูตรหารข้างต้นตรง ๆ ไม่ได้ `StandardScaler` มีวิธีจัดการคอลัมน์คงที่ตาม[เอกสาร](https://scikit-learn.org/1.6/modules/generated/sklearn.preprocessing.StandardScaler.html)

<span id="supervised-pipeline"></span>

## Pipeline เก็บการปรับสเกลกับโมเดลไว้ด้วยกัน

Pipeline เรียงขั้นตอนการเตรียม features และตัวโมเดลเข้าด้วยกัน เมื่อเรียก `.fit` จะ fit ตัวปรับสเกลจากข้อมูลฝึก แล้วส่งค่าที่แปลงแล้วไปฝึก KNN เมื่อ `.predict` จะใช้ตัวปรับสเกลเดิมกับข้อมูลใหม่ก่อนพยากรณ์ จึงช่วยลดการเผลอปรับสเกล train กับ test คนละชุด

```python
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

raw_knn = KNeighborsClassifier(n_neighbors=1).fit(scale_train, scale_labels)
scaled_knn = make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=1))
scaled_knn.fit(scale_train, scale_labels)
print("Raw / standardized prediction:", raw_knn.predict(scale_query), scaled_knn.predict(scale_query))
print("Scaler mean:", scaled_knn.named_steps["standardscaler"].mean_)
print("Scaler SD:", scaled_knn.named_steps["standardscaler"].scale_)
```

ผลคำตอบดิบคือ `[0]` และหลัง standardize คือ `[1]` ตรงกับการคำนวณระยะทางด้วยมือ `named_steps` ช่วยเปิดดูขั้นตอนที่อยู่ภายใน Pipeline ค่าที่เก็บใน `mean_` และ `scale_` ตรงกับสถิติจากข้อมูลฝึกทั้งสามแถว

Pipeline ไม่ได้ป้องกันข้อมูลรั่วได้เองทุกกรณี หากส่ง features ที่สร้างจากอนาคตหรือเลือกแถวทดสอบเข้ามาใน `.fit` ผลก็ยังรั่วอยู่ เราจะตรวจทั้งการสร้าง features การแบ่งเวลา และขอบเขตที่แต่ละขั้นตอนเห็นข้อมูลใน[บทการทดสอบโมเดล](model-validation.html)

<span id="supervised-svm"></span>

## SVM เลือกเส้นแบ่งพร้อมระยะเผื่อ

Support vector machine หรือ SVM เป็นอีกวิธีที่คอร์สแนะนำ Linear SVM สร้างคะแนน $f(x)=w^{\mathsf T}x+b$ แล้วใช้ด้านของเส้น $f(x)=0$ แยก class การ fit พิจารณาระยะเผื่อหรือ margin ร่วมกับโทษจากจุดที่ผิดเงื่อนไข ตัวแปร C ควบคุมการแลกระหว่างสองส่วนตามนิยามของ SVM

ตัวอย่างสอง features ต่อไปแยก class ได้ด้วยเส้น $x_1=1$ จุดฝั่งซ้ายมี feature แรกเท่ากับศูนย์และ label 0 ส่วนฝั่งขวามี feature แรกเท่ากับสองและ label 1 ทั้งสอง features เป็นพิกัดไม่มีหน่วยในตัวอย่างนี้

```python
from sklearn.svm import SVC

svm_X = np.array([[0.0, 0.0], [0.0, 1.0], [2.0, 0.0], [2.0, 1.0]])
svm_y = np.array([0, 0, 1, 1])
linear_svm = SVC(kernel="linear", C=100.0)
linear_svm.fit(svm_X, svm_y)
svm_queries = np.array([[0.5, 0.5], [1.5, 0.5]])
print("Coefficient / intercept:", linear_svm.coef_, linear_svm.intercept_)
print("Decision scores:", linear_svm.decision_function(svm_queries))
print("Classes:", linear_svm.predict(svm_queries))
```

ได้ coefficient `[1,0]` และ intercept −1 จึงมีคะแนน $f(x)=x_1-1$ คะแนนของสองจุดใหม่คือ −0.5 และ +0.5 ให้ class 0 และ 1 ตามลำดับ `decision_function` เป็นคะแนนจากเส้นแบ่ง ไม่ใช่ probability ระหว่างศูนย์กับหนึ่ง และ C ที่กำหนดเป็นค่าประกอบตัวอย่าง ไม่ได้เลือกจากการค้นหาบน test

SVM ยังมีสมมติฐานผ่าน kernel, margin, penalty และสเกล features การใช้วิธีนี้จึงไม่ได้ทำให้ปัญหาปราศจากสมมติฐาน ส่วน nonlinear kernel เพิ่มความยืดหยุ่นของเส้นแบ่งและต้องตรวจการเลือกพารามิเตอร์เช่นเดียวกัน ดู [scikit-learn: Support Vector Machines](https://scikit-learn.org/1.6/modules/svm.html#classification)

<span id="supervised-exercises"></span>

## แบบฝึกหัดพร้อมเฉลย

### 1. Slope ใช้หน่วยอะไร

จาก $\hat y=0.002+0.006x$ ถ้า score เพิ่มจาก 1 เป็น 2 ค่าพยากรณ์เปลี่ยนเท่าไร

เฉลย: เปลี่ยนจาก 0.008 เป็น 0.014 หรือจาก 0.8% เป็น 1.4% ต่อเดือน จึงเพิ่ม 0.6 จุดเปอร์เซ็นต์ สัมประสิทธิ์มีหน่วยผลตอบแทนทศนิยมต่อหนึ่งหน่วย score

### 2. ใช้ค่าเฉลี่ย Test เป็น Baseline ได้หรือไม่

เฉลย: ถ้าต้องการ baseline ที่พยากรณ์ได้จริงก่อนรู้คำตอบ ต้องใช้ค่าเฉลี่ยจากข้อมูลฝึก การใช้ target ของ test หา baseline ทำให้ baseline เห็นคำตอบที่จะใช้ประเมินอยู่แล้ว ตัวอย่างจึงใช้ 0.005 จาก train ทุกแถว

### 3. Log loss ลงโทษความมั่นใจผิดอย่างไร

เมื่อ $y=1$ ให้เปรียบเทียบ probability 0.9 กับ 0.1

เฉลย: Loss คือ $-\log(0.9)\approx0.10536$ และ $-\log(0.1)\approx2.30259$ ตามลำดับ การให้โอกาส class ที่เกิดจริงเพียง 10% จึงเสียคะแนนมากกว่า แม้การแปลงเป็น class จะนับการพลาดเป็นหนึ่งครั้งเท่านั้น

### 4. อ่าน Confusion Matrix

ให้ตาราง `[[8,2],[3,7]]` ตามแถวจริงและคอลัมน์ที่ทายเป็น 0/1 จงหา accuracy, precision และ recall

เฉลย: $TN=8,FP=2,FN=3,TP=7$ ดังนั้น accuracy $=(8+7)/20=75$%, precision $=7/9\approx77.78$% และ recall $=7/10=70$% ตัวหารต่างกันเพราะแต่ละตัวตอบคนละคำถาม

### 5. KNN เปลี่ยน K แล้วคำตอบเปลี่ยนได้อย่างไร

เพื่อนบ้านเรียงใกล้ไปไกลมี labels `[0,1,1,0,1]` จงทายด้วย K เท่ากับ 1, 3 และ 5 แบบถ่วงเท่ากัน

เฉลย: K=1 ทาย 0, K=3 ทาย 1 จากเสียงสองในสาม และ K=5 ทาย 1 จากเสียงสามในห้า ข้อมูลใหม่นี้ยังไม่บอกว่าค่าใดแม่นที่สุด ต้องประเมินกับ validation ที่ไม่ใช้ฝึกเพื่อนบ้าน

### 6. เปลี่ยนล้านบาทเป็นบาทต้องเปลี่ยนความหมายของโมเดลหรือไม่

ถ้าเปลี่ยน feature ปริมาณซื้อขายจากล้านบาทเป็นบาทโดยคูณหนึ่งล้าน ระยะทางดิบจะเปลี่ยนหรือไม่ แล้วค่ามาตรฐานจาก train จะเป็นอย่างไร

เฉลย: ระยะทางดิบจะถูกครอบงำโดยคอลัมน์นี้มากขึ้น เพราะส่วนต่างโตหนึ่งล้านเท่า แต่ถ้าคำนวณค่าเฉลี่ยและ SD ของคอลัมน์ใหม่จาก train แล้ว standardize ทั้งสองสถิติก็โตหนึ่งล้านเท่าเช่นกัน จึงได้ z-score เดิมสำหรับการเปลี่ยนหน่วยเชิงบวกนี้

### 7. คะแนน SVM เท่ากับ 2 แปลว่าความน่าจะเป็น 200% หรือไม่

เฉลย: ไม่ใช่ `decision_function` คืนคะแนนด้านและขนาดตามเส้นแบ่ง ซึ่งไม่ได้ถูกจำกัดในช่วง 0–1 หากต้องใช้ probability ต้องมีวิธีประมาณและตรวจ calibration เพิ่มเติม จะอ่านคะแนนดิบเป็น probability โดยตรงไม่ได้

### 8. Test Score ดีครั้งเดียวเพียงพอหรือไม่

ตัวอย่างเส้นตรงมี test RMSE ต่ำกว่า baseline มาก เราควรสรุปว่าโมเดลใช้ลงทุนจริงได้หรือไม่

เฉลย: ยังไม่ได้ เพราะเป็นข้อมูลสมมติที่มีความสัมพันธ์ตามการออกแบบและมีเพียงสาม observations สำหรับประเมิน ต้องมีข้อมูลที่ตรงกับงานจริง ตรวจเวลาเผยแพร่ข้อมูล ขอบเขตการเลือกโมเดล ความไม่แน่นอน และผลของต้นทุนกับกฎลงทุนต่อไป

บท[ทดสอบโมเดลโดยไม่เห็นอนาคต](model-validation.html)จะขยายจากการ fit ครั้งเดียวไปสู่การเลือก K และตรวจโมเดลด้วยลำดับเวลาที่กำหนดไว้ก่อนดูผล

<span id="supervised-sources"></span>

## แหล่งที่มาและขอบเขต

อ่าน Transcript เต็มของ [Supervised learning](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/U2fjL/supervised-learning) และ [First algorithms](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/AbO02/first-algorithms) เมื่อ 3 ตุลาคม 2026 ใช้เป็นหัวข้อประกอบการเรียน ตัวอย่างในหน้านี้ใช้คะแนนและ labels ที่สร้างขึ้นใหม่ และแยก objective ของ OLS, logistic regression และ SVM ให้ชัด

ตรวจสูตรและการใช้ API กับเอกสาร scikit-learn 1.6 ได้แก่ [Linear models](https://scikit-learn.org/1.6/modules/linear_model.html), [Nearest neighbors](https://scikit-learn.org/1.6/modules/neighbors.html), [StandardScaler](https://scikit-learn.org/1.6/modules/generated/sklearn.preprocessing.StandardScaler.html), [Confusion matrix](https://scikit-learn.org/1.6/modules/generated/sklearn.metrics.confusion_matrix.html) และ [Support vector machines](https://scikit-learn.org/1.6/modules/svm.html) ตัวเลขที่รายงานมาจากการรันตัวอย่างเหล่านี้โดยไม่มีข้อมูลตลาดหรือโค้ดต้นทางของคอร์ส
