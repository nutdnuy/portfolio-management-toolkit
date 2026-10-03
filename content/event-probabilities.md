---
title: "พยากรณ์เหตุการณ์: ความน่าจะเป็นบอกอะไร"
description: แยก Recession ออกจากตลาดขาลง กำหนดเวลาของ Target และข้อมูลที่เผยแพร่จริง แล้วอ่าน Odds, Brier Score, Log Loss และ Threshold จากตัวอย่างเล็ก
---

# พยากรณ์เหตุการณ์: ความน่าจะเป็นบอกอะไร

<p class="lead">ถ้าโมเดลบอกว่าเดือนหน้ามีโอกาสเกิดเหตุการณ์ 30% เราจะรู้ได้อย่างไรว่าเป็นคำพยากรณ์ที่มีประโยชน์?</p>

ก่อนหน้านี้เราใช้แบบจำลองเพื่อประมาณผลตอบแทนหรือแบ่งกลุ่มสินทรัพย์ คราวนี้คำตอบเป็นเหตุการณ์สองแบบ: เกิดหรือไม่เกิด เราจึงต้องระบุทั้งเหตุการณ์ที่สนใจ ช่วงเวลาที่พยากรณ์ และเวลาที่สามารถตรวจคำตอบจริงได้ ความน่าจะเป็น 30% ไม่ได้บอกว่าเหตุการณ์จะเกิดแน่นอน และการทายผิดครั้งเดียวก็ยังไม่พอจะตัดสินว่าความน่าจะเป็นนั้นใช้ไม่ได้

บทนี้ต่อจาก[การวิเคราะห์ภาวะตลาด](market-regimes.html) และปูพื้นฐานสำหรับ [Lab พยากรณ์เหตุการณ์](recession-models.html) ใช้ตัวเลขสมมติทั้งหมด รัน Notebook แยกได้ด้วย NumPy, pandas และ scikit-learn ตัวอย่างไม่ได้ประเมินโอกาสเกิด Recession ของประเทศใดในปัจจุบัน

## กำหนดเหตุการณ์ให้เป็นประโยคที่ตรวจได้

คำว่า Recession, ตลาดหุ้นตก และความผันผวนสูงไม่ได้มีความหมายเดียวกัน เศรษฐกิจอาจหดตัวในช่วงที่หุ้นเริ่มฟื้น หรือหุ้นตกโดยที่เศรษฐกิจยังไม่เข้าเกณฑ์ถดถอยก็ได้ ถ้าสร้าง label จากผลตอบแทนหุ้น แล้วเรียกสิ่งนั้นว่า Recession โมเดลจะตอบคนละคำถามกับชื่อที่ตั้งไว้

สำหรับสหรัฐฯ [NBER](https://www.nber.org/research/business-cycle-dating) กำหนดจุดเปลี่ยนของวัฏจักรเศรษฐกิจจากหลักฐานกิจกรรมทางเศรษฐกิจหลายด้าน การกำหนดวันที่เกิดเหตุการณ์เป็นงานย้อนหลัง และวันที่ประกาศอาจช้ากว่าวันที่เหตุการณ์เริ่มขึ้น ดู[วันที่ประกาศอย่างเป็นทางการ](https://www.nber.org/research/business-cycle-dating/business-cycle-dating-committee-announcements) จึงต้องแยกวันที่ที่ label อธิบายออกจากวันที่ผู้วิจัยรู้ label นั้น

| ตัวอย่างโจทย์ | สิ่งที่กำหนดเป็น 1 | สิ่งที่ยังต้องระบุ |
|---|---|---|
| Nowcast เศรษฐกิจ | เดือนปัจจุบันอยู่ในภาวะถดถอย | ข้อมูลเดือนนี้เผยแพร่แล้วหรือยัง |
| Forecast เศรษฐกิจ | เดือนที่อยู่ห่างออกไปสามเดือนอยู่ในภาวะถดถอย | พยากรณ์เดือนเดียวหรืออย่างน้อยหนึ่งเดือนในช่วงสามเดือน |
| พยากรณ์ผลตอบแทนติดลบ | ผลตอบแทนหุ้นเดือนหน้าต่ำกว่า 0 | ใช้ราคาอย่างเดียวหรือ Total Return |
| พยากรณ์เหตุการณ์รุนแรง | ผลตอบแทนเดือนหน้าต่ำกว่า −10% | เกณฑ์ −10% เลือกไว้ก่อนหรือเลือกหลังดูผล |

ให้ $y_{t+h}$ เป็น [target](glossary.html#target-label) ที่เกิดในเดือน $t+h$, $h$ เป็นจำนวนเดือนที่มองล่วงหน้า และ $\mathcal I_t$ เป็นข้อมูลที่รู้จริงเมื่อจบเดือน $t$:

$$
p_t=P(y_{t+h}=1\mid\mathcal I_t).
$$

ถ้า $h=0$ เรากำลังประมาณภาวะปัจจุบันหรือ nowcasting ถ้า $h=3$ เรากำลังพยากรณ์ล่วงหน้าสามเดือน ผลทดสอบ nowcast ที่ดีไม่ใช่หลักฐานว่าโมเดลพยากรณ์ล่วงหน้าสามเดือนได้ดีเท่ากัน

### หนึ่งเดือนกับ “อย่างน้อยหนึ่งครั้งในสามเดือน”

สร้าง label สองแบบจากลำดับเดียวกัน `shift(-3)` ดึงค่าในอนาคตมาเป็นคำตอบสำหรับประเมินภายหลัง ไม่ใช่ feature ที่อนุญาตให้ใช้ในวันพยากรณ์ `concat` รวมหลายคอลัมน์ ส่วน `skipna=False` ทำให้ช่วงปลายที่ยังไม่ครบสามเดือนคงเป็นข้อมูลขาดหาย

```python
import numpy as np
import pandas as pd

states = pd.Series([0, 0, 1, 0, 0, 1, 1, 0], name="event")
future_three = pd.concat([states.shift(-j) for j in (1, 2, 3)], axis=1)
label_exact = states.shift(-3)
label_any = future_three.max(axis=1, skipna=False)
label_table = pd.DataFrame({"at_t": states, "exact_t_plus_3": label_exact,
                            "any_next_3": label_any})
print(label_table.to_string(index=True))
```

ที่แถว $t=0$ อีกสามเดือนมี label 0 แต่ในช่วงเดือน 1–3 มีเหตุการณ์ที่เดือน 2 จึงได้ `any_next_3=1` สองคอลัมน์นี้ต่างกันตั้งแต่คำนิยาม หากไม่ระบุ horizon ให้ชัด จะเปรียบเทียบคะแนนของโมเดลกันไม่ได้

## เวลาที่ข้อมูลเกิดกับเวลาที่ข้อมูลพร้อมใช้

สมมติเราออกคำพยากรณ์สิ้นเดือน 10 มองล่วงหน้าสามเดือน และหน่วยงานประกาศ label ช้าสองเดือน ข้อมูลฝึกที่เริ่มจากเดือน 5 มีคำตอบอยู่เดือน 8 และประกาศเดือน 10 จึงใช้ได้ แต่แถวเริ่มเดือน 6 ต้องรอประกาศเดือน 11

ในตัวอย่างนี้ตัวเลขเดือนเป็นลำดับสมมติ เรากำหนดว่าการประกาศเกิดก่อนจุดตัดสินใจสิ้นเดือนนั้น ในงานจริงควรใช้ timestamp และเขตเวลาให้ละเอียดพอ

```python
origin = np.arange(1, 13)
horizon = 3
announcement_delay = 2
availability = pd.DataFrame({"origin": origin,
                              "target_month": origin + horizon,
                              "label_available": origin + horizon + announcement_delay})
cutoff = 10
eligible = availability[availability["label_available"] <= cutoff]
print(eligible.to_string(index=False))
print("Latest usable origin:", int(eligible["origin"].max()))
```

แถวสุดท้ายที่ใช้ฝึกได้เริ่มเดือน 5 แม้มีตาราง label ของทั้ง 12 แถวอยู่ในไฟล์วันนี้ ก็ไม่ได้แปลว่า label ทุกแถวนั้นพร้อมใช้ในเดือน 10 การเว้น gap ตาม horizon อย่างเดียวจึงอาจไม่พอ หากมีการประกาศล่าช้าเพิ่มเติม

ข้อมูลเศรษฐกิจยังมีการแก้ไขย้อนหลังด้วย ค่า GDP ที่ดาวน์โหลดวันนี้อาจไม่เท่ากับค่าที่เผยแพร่ครั้งแรก [FRED/ALFRED](https://fred.stlouisfed.org/docs/api/fred/realtime_period.html) แยกเวลาของ observation ออกจากช่วงเวลาที่ข้อมูลรุ่นนั้นเป็นที่รู้จัก การทดสอบที่ตั้งใจจำลองการตัดสินใจในอดีตควรเลือกข้อมูลรุ่นที่มีอยู่ในวันนั้น การเลื่อนข้อมูลฉบับล่าสุดย้อนหลังหนึ่งเดือนแก้ปัญหาการปรับปรุงตัวเลขย้อนหลังไม่ได้ทั้งหมด

## จากความน่าจะเป็นสู่ Odds และ Log-odds

[Logistic regression](supervised-learning.html) ใช้คะแนนเชิงเส้น $z=b+\beta^\top x$ แล้วแปลงเป็นความน่าจะเป็นด้วย sigmoid:

$$
p=\frac{1}{1+e^{-z}},\qquad
\text{odds}=\frac{p}{1-p},\qquad
\log(\text{odds})=z.
$$

ถ้าโอกาสเกิดเหตุการณ์เท่ากับ 20% จะได้ odds $0.2/0.8=0.25$ หรือเกิดหนึ่งส่วนต่อไม่เกิดสี่ส่วน ไม่ใช่ความน่าจะเป็น 25% ส่วน log-odds เท่ากับประมาณ −1.3863 `np.log` เป็น logarithm ฐาน $e$ และ `exp` เป็นฟังก์ชันผกผัน

```python
probability = 0.20
odds = probability / (1 - probability)
log_odds = np.log(odds)
recovered_probability = 1 / (1 + np.exp(-log_odds))
print(f"Odds: {odds:.4f}")
print(f"Log-odds: {log_odds:.4f}")
print(f"Probability recovered: {recovered_probability:.2%}")
```

ค่าสัมประสิทธิ์ logistic อยู่บนสเกล log-odds ถ้า coefficient ของ feature เท่ากับ 0.7 การเพิ่ม feature หนึ่งหน่วยจะคูณ odds ด้วย $e^{0.7}$ ภายใต้แบบจำลองที่กำหนดและตรึง feature อื่นไว้ ไม่ได้เพิ่ม probability ตายตัว 70 จุดเปอร์เซ็นต์ และไม่ได้เป็นหลักฐานเชิงเหตุและผล

## Accuracy สูงอาจพลาดเหตุการณ์ทั้งหมด

สมมติมี 20 เดือน เกิดเหตุการณ์เพียงสองเดือน โมเดลที่ทายว่าไม่เกิดเสมอจะตอบถูก 18 เดือน ได้ accuracy 90% แต่ตรวจเจอเหตุการณ์จริงศูนย์ครั้ง

```python
rare_y = np.array([0] * 18 + [1, 1])
always_normal = np.zeros_like(rare_y)
accuracy_baseline = np.mean(always_normal == rare_y)
recall_baseline = np.sum((always_normal == 1) & (rare_y == 1)) / np.sum(rare_y == 1)
print(f"Always-normal accuracy: {accuracy_baseline:.1%}")
print(f"Event recall: {recall_baseline:.1%}")
```

จำนวนเดือนที่มีเหตุการณ์ก็ไม่เท่ากับจำนวนเหตุการณ์อิสระ ภาวะถดถอยหนึ่งครั้งอาจมีหลายเดือนติดกัน การสุ่มแยกเดือนใกล้เคียงกันไปอยู่ทั้งชุดฝึกและชุดทดสอบทำให้การประเมินง่ายกว่าการเจอวิกฤตครั้งใหม่ ควรรายงานจำนวนช่วงเหตุการณ์ พร้อมผลแยกตามช่วงเวลาและการทดสอบตามลำดับเวลา

## คะแนนของความน่าจะเป็น: Brier และ Log Loss

ใช้สี่คำพยากรณ์สมมติ $p=(0.10,0.40,0.35,0.80)$ กับผลจริง $y=(0,0,1,1)$ [Brier score](glossary.html#brier-score) คือค่าเฉลี่ย squared error ของ probability:

$$
\operatorname{Brier}=\frac{1}{n}\sum_{i=1}^n(p_i-y_i)^2.
$$

พจน์ทั้งสี่เป็น $0.01,0.16,0.4225,0.04$ จึงได้ $0.158125$ คะแนนยิ่งต่ำยิ่งดีภายใต้ scoring rule นี้ บางเอกสารใช้ชื่อ Quadratic Probability Score หรือ QPS และนิยามเป็นสองเท่าของ Brier จึงต้องดูสูตรก่อนเทียบตัวเลข

```python
y = np.array([0, 0, 1, 1])
p = np.array([0.10, 0.40, 0.35, 0.80])
squared_errors = (p - y) ** 2
brier = squared_errors.mean()
qps_twice_brier = 2 * brier
print("Squared errors:", squared_errors)
print(f"Brier: {brier:.6f}")
print(f"QPS using twice-Brier convention: {qps_twice_brier:.6f}")
```

[Log loss](glossary.html#log-loss) ให้ค่าปรับสูงมากกับการมั่นใจผิด ถ้าเหตุการณ์เกิด แต่ให้ probability ใกล้ศูนย์ ค่า $-\log p$ จะสูง:

$$
L=-\frac{1}{n}\sum_i\left[y_i\log p_i+(1-y_i)\log(1-p_i)\right].
$$

```python
safe_p = np.clip(p, 1e-12, 1 - 1e-12)
log_loss_manual = -np.mean(y * np.log(safe_p) + (1 - y) * np.log1p(-safe_p))
from sklearn.metrics import brier_score_loss, log_loss
print(f"Log loss: {log_loss_manual:.6f}")
print("Library Brier agrees:", np.isclose(brier, brier_score_loss(y, p)))
print("Library log loss agrees:", np.isclose(log_loss_manual, log_loss(y, p)))
```

`clip` ใช้ป้องกันการคำนวณ log ของศูนย์ ส่วน `log1p(-p)` คำนวณ $\log(1-p)$ อย่านำค่าที่ clip ไปตีความว่าโมเดลได้รับการปรับ calibration แล้ว คะแนนต่ำลงอาจสะท้อนทั้งการจัดลำดับและคุณภาพของ probability จึงไม่ใช่การตรวจ calibration เพียงอย่างเดียว

## Threshold เปลี่ยนการตัดสินใจ แต่ไม่เปลี่ยน Probability

ถ้าจัดเป็นเหตุการณ์เมื่อ $p\geq0.5$ ตัวอย่างสี่เดือนจะตรวจเจอหนึ่งในสองเหตุการณ์ ถ้าเปลี่ยน threshold เป็น 0.3 จะตรวจเจอทั้งสองครั้ง แต่เพิ่มการเตือนผิดอีกหนึ่งครั้ง

```python
def event_counts(actual, probability, threshold):
    predicted = probability >= threshold
    positive = actual == 1
    return {
        "TP": int(np.sum(predicted & positive)),
        "FP": int(np.sum(predicted & ~positive)),
        "TN": int(np.sum(~predicted & ~positive)),
        "FN": int(np.sum(~predicted & positive)),
    }

threshold_counts = {threshold: event_counts(y, p, threshold) for threshold in (0.5, 0.3)}
print(pd.DataFrame(threshold_counts).T.to_string())
```

TP คือเตือนแล้วเกิดจริง, FP คือเตือนแต่ไม่เกิด, TN คือไม่เตือนและไม่เกิด, FN คือไม่เตือนแต่เกิดจริง สี่จำนวนนี้ประกอบเป็น [confusion matrix](glossary.html#confusion-matrix) โดยต้องระบุลำดับแถวและคอลัมน์ให้ชัด

$$
\text{precision}=\frac{TP}{TP+FP},\qquad
\text{recall}=\frac{TP}{TP+FN}.
$$

ที่ threshold 0.5 precision เท่ากับ 1 และ recall เท่ากับ 0.5 ที่ threshold 0.3 precision เท่ากับ $2/3$ และ recall เท่ากับ 1 ทั้งสองใช้ probability ชุดเดิม เลือก threshold ด้วยวัตถุประสงค์และข้อมูล validation ก่อนเปิดผล test

### เลือก Threshold จากต้นทุนที่ระบุไว้

สมมติการเตือนผิดเสีย 3 หน่วย การพลาดเหตุการณ์เสีย 12 หน่วย ส่วนการเตือนถูกและการไม่เตือนถูกเสียศูนย์ หาก probability เชื่อถือได้ ต้นทุนคาดหวังของการเตือนคือ $3(1-p)$ และของการไม่เตือนคือ $12p$ จึงควรเตือนในโจทย์นี้เมื่อ

$$
3(1-p)<12p\quad\Longleftrightarrow\quad p>\frac{3}{3+12}=0.2.
$$

```python
false_alarm_cost = 3.0
miss_cost = 12.0
cost_threshold = false_alarm_cost / (false_alarm_cost + miss_cost)
warn_expected_cost = false_alarm_cost * (1 - p)
quiet_expected_cost = miss_cost * p
print(f"Cost-derived threshold: {cost_threshold:.2f}")
print("Warn cost:", warn_expected_cost)
print("No-warning cost:", quiet_expected_cost)
```

นี่คือตารางต้นทุนสมมติที่ตั้งไว้เพื่อฝึกตัดสินใจ ยังไม่ใช่กฎขายหุ้น พอร์ตจริงมีผลตอบแทน ต้นทุนซื้อขาย สินทรัพย์ทดแทน และข้อจำกัดเพิ่ม การพยากรณ์ Recession ถูกจึงไม่รับประกันว่าการลดหุ้นจะให้ผลตอบแทนดีกว่า

## การจัดลำดับกับ Calibration เป็นคนละคำถาม

ROC-AUC วัดความสามารถในการจัดอันดับ โดยในกรณี binary มีความหมายเท่ากับสัดส่วนคู่ที่เหตุการณ์จริงได้ probability สูงกว่ากรณีไม่เกิด พร้อมให้ครึ่งคะแนนเมื่อเสมอ ตัวอย่างนี้มีคู่เปรียบเทียบ $2\times2=4$ คู่ ชนะสามคู่จึงได้ AUC 0.75

```python
from sklearn.metrics import roc_auc_score, average_precision_score, matthews_corrcoef
positive_p = p[y == 1]
negative_p = p[y == 0]
pair_scores = [(a > b) + 0.5 * (a == b) for a in positive_p for b in negative_p]
auc_manual = np.mean(pair_scores)
print(f"Pairwise AUC: {auc_manual:.4f}")
print(f"Library AUC: {roc_auc_score(y, p):.4f}")
print(f"Average precision: {average_precision_score(y, p):.4f}")
print(f"MCC at 0.5: {matthews_corrcoef(y, p >= 0.5):.4f}")
```

Average precision สรุป precision–recall โดยให้น้ำหนักตามการเปลี่ยน recall ไม่ใช่ ROC-AUC ส่วน Matthews correlation coefficient หรือ MCC ใช้ทั้งสี่ช่องของ confusion matrix มีช่วง −1 ถึง 1 และเทียบการสอดคล้องของ label ที่ทายกับ label จริง โมเดลที่ทาย class เดียวทั้งหมดอาจทำให้สูตรมีตัวหารศูนย์ ต้องระบุ convention ของเครื่องมือที่ใช้

สำหรับ [calibration](glossary.html#probability-calibration) เราถามว่า ในกลุ่มที่ให้ probability ประมาณ 20% เหตุการณ์เกิดจริงใกล้ 20% หรือไม่ ลองสร้างกลุ่มสมมติสองกลุ่มที่มีจำนวนครั้งแน่นอน:

```python
calibration_p = np.repeat([0.2, 0.8], 10)
calibration_y = np.array([1, 1] + [0] * 8 + [1] * 8 + [0, 0])
calibration_table = pd.DataFrame({"p": calibration_p, "y": calibration_y}).groupby("p").agg(
    observations=("y", "size"), event_rate=("y", "mean")
)
print(calibration_table.to_string())
```

ในข้อมูลที่จงใจสร้างนี้ อัตราเกิดเหตุการณ์ตรง probability ของแต่ละกลุ่มพอดี แต่แต่ละกลุ่มมีเพียงสิบครั้ง และเราเป็นคนกำหนดผลเอง จึงไม่ได้พิสูจน์ว่าโมเดลใด calibrated ในตลาดจริง กราฟ calibration ควรแสดงจำนวนตัวอย่างในแต่ละ bin พร้อมประเมินบนข้อมูลที่ไม่ใช้ปรับ probability หากข้อมูลช่วงทดสอบมี class เดียว ROC-AUC จะนิยามไม่ได้ แม้ Brier และ log loss ยังประเมินได้โดยระบุ label ให้ครบ

## แบบฝึกหัด

<details><summary>1. โมเดล Nowcast ได้ accuracy 96% ใช้อ้างว่าพยากรณ์ล่วงหน้าสามเดือนได้ 96% หรือไม่?</summary>
<p>ไม่ได้ ต้องเปลี่ยน target เป็นเดือนที่ห่างออกไปสามเดือน สร้างข้อมูลตามเวลาที่ใช้ได้ และประเมินใหม่บนช่วงทดสอบที่กันไว้ Nowcast กับ forecast ตอบคนละ horizon</p>
</details>

<details><summary>2. โอกาสเกิดเหตุการณ์ 25% มี odds และ log-odds เท่าไร?</summary>
<p>Odds เท่ากับ 0.25/0.75 = 1/3 ส่วน log-odds เท่ากับ log(1/3) ≈ −1.0986 ถ้า odds เท่ากับ 1 จะได้ probability 50%</p>
</details>

<details><summary>3. ที่ cutoff เดือน 10 ถ้า horizon เหลือหนึ่งเดือนและประกาศช้าสองเดือน ใช้ origin ล่าสุดเท่าไร?</summary>
<p>ต้องมี origin + 1 + 2 ≤ 10 จึงใช้ origin ล่าสุดเดือน 7 ภายใต้สมมติฐานว่าประกาศก่อนเวลาตัดสินใจสิ้นเดือน</p>
</details>

<details><summary>4. ถ้าข้อมูล 100 เดือนมีเหตุการณ์ห้าเดือน baseline ที่ไม่เตือนเลยได้ accuracy เท่าไร?</summary>
<p>95% แต่ recall ของเหตุการณ์เป็นศูนย์ จำนวนเดือนทั้งหมดอย่างเดียวจึงไม่บอกว่าโจทย์มีเหตุการณ์ให้เรียนรู้เพียงพอหรือไม่</p>
</details>

<details><summary>5. ให้ probability 0.2 แต่เกิดเหตุการณ์จริง Brier contribution และ log-loss contribution เท่าไร?</summary>
<p>Squared error เท่ากับ (0.2−1)² = 0.64 และ log loss เท่ากับ −log(0.2) ≈ 1.6094 ทั้งสองเป็น contribution ของหนึ่ง observation ก่อนนำไปเฉลี่ย</p>
</details>

<details><summary>6. โมเดล A มี AUC สูงกว่า B แปลว่า probability ของ A calibrated ดีกว่าหรือไม่?</summary>
<p>ไม่จำเป็น AUC ดูการจัดอันดับ การแปลง probability ด้วยฟังก์ชันเพิ่มอย่างเคร่งครัดอาจคงอันดับเดิมแต่ทำให้ calibration แย่ลง ต้องดูทั้ง scoring rule และความสัมพันธ์ระหว่าง predicted probability กับ event rate</p>
</details>

<details><summary>7. เลือก threshold ที่ทำกำไรดีที่สุดจาก final test แล้วรายงานผลเดิมได้หรือไม่?</summary>
<p>ผลนั้นกลายเป็นผลที่ใช้เลือกกฎแล้ว จึงไม่ใช่การประเมิน final test ที่ไม่เคยใช้ ต้องนำกฎที่เลือกไปประเมินกับข้อมูลใหม่ หรือออกแบบการเลือก threshold ภายใน validation ตามลำดับเวลาก่อน</p>
</details>

อ่านต่อ [สร้างและเปรียบเทียบโมเดลพยากรณ์](recession-models.html) ซึ่งจะใช้ตารางวันที่พร้อมใช้ของ feature และ label เป็นส่วนหนึ่งของโค้ดฝึกทุกครั้ง
