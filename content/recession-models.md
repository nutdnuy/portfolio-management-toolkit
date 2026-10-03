---
title: "Lab: ทดสอบโมเดลพยากรณ์เหตุการณ์ตามเวลา"
description: สร้างข้อมูลสมมติที่รู้เวลาประกาศ เปรียบเทียบ Logistic, Tree, Forest และ Boosting ด้วย validation ตามเวลา แล้วทดสอบแบบ rolling โดยกัน label ที่ยังไม่พร้อมใช้
---

# Lab: ทดสอบโมเดลพยากรณ์เหตุการณ์ตามเวลา

<p class="lead">ก่อนถามว่าโมเดลไหนเก่งกว่า ต้องตรวจให้ได้ก่อนว่าแต่ละโมเดลเห็นข้อมูลอะไรตอนออกคำพยากรณ์</p>

บท [ความน่าจะเป็นของเหตุการณ์](event-probabilities.html) แยกคะแนน probability ออกจากการเตือนที่ใช้ threshold แล้ว บทนี้จะสร้างกระบวนการตั้งแต่ข้อมูลไปจนถึงคำพยากรณ์ โดยเปรียบเทียบ Logistic regression, Decision tree, Random forest และ Gradient boosting บนวันตัดสินใจชุดเดียวกัน

ใช้ข้อมูลจำลอง 240 เดือน ไม่ใช่ข้อมูล Recession จริง และไม่ได้ทำซ้ำคะแนนจากวิดีโอคอร์ส การจำลองช่วยให้เรารู้แน่ชัดว่า feature และ label พร้อมใช้เมื่อไร ส่วนการนำวิธีเดียวกันไปใช้กับข้อมูลเศรษฐกิจต้องมีวันที่เผยแพร่และข้อมูลแต่ละรุ่นเพิ่ม ตัวอย่างรันด้วย NumPy, pandas, SciPy และ scikit-learn 1.6.1 ทุก Python block รันต่อกันใน Notebook ของบทนี้ได้

## ระบุสิ่งที่สมมติก่อนสร้างข้อมูล

เราสร้างภาวะแฝง $s_t$ ที่มีความต่อเนื่อง:

$$
s_t=0.75s_{t-1}+0.65\epsilon_t,\qquad \epsilon_t\sim N(0,1).
$$

คำว่า “แฝง” หมายถึงโมเดลที่เราฝึกไม่ได้เห็น $s_t$ โดยตรง เราใช้มันเฉพาะตอนสร้างข้อมูล จากนั้นแปลงภาวะเป็น probability ของเหตุการณ์ในเดือนเดียวกัน:

$$
q_t=\operatorname{sigmoid}\left(-1.3+1.2s_t+0.5\mathbf 1\{s_t>1\}\right),
\qquad y_t\sim\operatorname{Bernoulli}(q_t).
$$

Bernoulli คือการสุ่มผลสองแบบ ได้ 1 ด้วย probability $q_t$ และได้ 0 ด้วย probability $1-q_t$ พจน์ indicator $\mathbf 1\{s_t>1\}$ มีค่า 1 เมื่อเงื่อนไขเป็นจริง จึงเพิ่มความไม่เป็นเส้นตรงไว้ในตัวอย่าง โมเดลที่ซับซ้อนกว่าอาจใช้ประโยชน์จากมันได้หรือไม่ได้เมื่อข้อมูลมีจำกัด

สมมติ feature สามกลุ่มมีเวลาพร้อมใช้ดังนี้:

| ข้อมูล | วิธีสร้างสมมติ | พร้อมใช้ |
|---|---|---|
| Indicator เศรษฐกิจ | ภาวะแฝงบวก noise ขนาด 0.2 | ช้าหนึ่งเดือน |
| Market indicator | ภาวะแฝงบวก noise ขนาด 0.6 | สิ้นเดือนเดียวกันก่อนออกคำพยากรณ์ |
| Noise feature | ตัวเลขสุ่มที่ไม่มีบทบาทในสมการเหตุการณ์ | สิ้นเดือนเดียวกัน |
| Event label | ผลสุ่ม Bernoulli | ช้าสองเดือนหลังเดือนที่เกิดเหตุการณ์ |

นี่เป็นสมมติฐานเวลาประกาศสำหรับข้อมูลจำลองโดยเฉพาะ ไม่ใช่ปฏิทินเผยแพร่ตัวเลขจริง เราจะพยากรณ์ $y_{t+1}$ เมื่อสิ้นเดือน $t$ จึงใช้ label ของแถวเริ่มเดือน $t$ ฝึกได้ตั้งแต่เดือน $t+3$

```python
import numpy as np
import pandas as pd

def make_event_data(seed=501):
    rng = np.random.default_rng(seed)
    n = 240
    signal = np.zeros(n)
    innovations = rng.normal(size=n)
    for t in range(1, n):
        signal[t] = 0.75 * signal[t - 1] + 0.65 * innovations[t]
    probability = 1 / (1 + np.exp(-(-1.3 + 1.2 * signal + 0.5 * (signal > 1))))
    event = (rng.uniform(size=n) < probability).astype(int)
    raw = pd.DataFrame({
        "month": np.arange(n),
        "indicator": signal + rng.normal(0, 0.2, n),
        "market": signal + rng.normal(0, 0.6, n),
        "noise": rng.normal(size=n),
        "event": event,
    })
    x = pd.DataFrame({"indicator_lag1": raw.indicator.shift(1),
                      "market": raw.market, "noise": raw.noise})
    x["indicator_change"] = x.indicator_lag1.diff()
    data = x.assign(origin=raw.month, target=raw.event.shift(-1),
                    label_available=raw.month + 3)
    return data.dropna().reset_index(drop=True)

data = make_event_data()
features = ["indicator_lag1", "market", "noise", "indicator_change"]
print(data.head().round(4).to_string(index=False))
print("Rows:", len(data), "Events:", int(data.target.sum()))
```

ได้ 237 แถว เริ่ม origin 2 ถึง 238 เพราะการทำ lag และ difference ทำให้สองแถวแรกไม่มีข้อมูลครบ และแถวสุดท้ายยังไม่มี target เดือนถัดไป `reset_index` จัดหมายเลขแถวใหม่ แต่เราเก็บ `origin` ไว้เป็นนาฬิกาของการทดลอง จึงไม่ควรใช้หมายเลขแถวแทนเดือนโดยไม่ตรวจ

`signal` และ `probability` ภายในฟังก์ชันไม่ถูกส่งออกมาเป็น features ถ้าใส่ probability จริงที่ใช้สร้าง label ลงในข้อมูลฝึก โมเดลจะได้ข้อมูลที่เราไม่ได้ตั้งใจให้ผู้พยากรณ์รู้

## อ่านหนึ่งแถวให้เป็นก่อนฝึกโมเดล

เมื่อออกคำพยากรณ์ที่ origin 120 เรารู้ `market` ของเดือน 120 และ `indicator_lag1` ที่อธิบายเดือน 119 แต่ยังไม่รู้ target ของแถวนี้ เพราะมันเป็นเหตุการณ์เดือน 121 ซึ่งจะประกาศเดือน 123

```python
cutoff_example = 120
available_training = data[data.label_available <= cutoff_example]
current_features = data[data.origin == cutoff_example]
print("Latest training origin:", int(available_training.origin.max()))
print("Latest label release:", int(available_training.label_available.max()))
print(current_features[["origin", "label_available"] + features].round(4).to_string(index=False))
```

แถวฝึกล่าสุดคือ origin 117 ต้องเว้น origin 118 และ 119 แม้สองเดือนนี้อยู่ก่อนวันตัดสินใจ เพราะยังไม่มีคำตอบที่พร้อมใช้ การทดสอบแบบนี้อาศัย `label_available` โดยตรง แทนการเดาว่า `shift` หนึ่งแถวเพียงพอหรือไม่

## ต้นไม้หนึ่งต้นแบ่งข้อมูลอย่างไร

Decision tree เลือก feature และจุดตัด แบ่งข้อมูลเป็นกลุ่มย่อย แล้วใช้สัดส่วน label ในใบไม้เป็น probability ในกรณี binary ถ้าใบไม้มีเหตุการณ์ 2 จาก 10 ตัวอย่าง probability ที่ได้จะเป็น 0.2 ก่อนพิจารณาการปรับ calibration

ตัวอย่างเล็กมี feature $x=0,1,2,3,4,5$ และ label $0,0,0,1,1,1$ จุดตัด 2.5 แยกสองกลุ่มบริสุทธิ์ได้ วัดความปนกันด้วย Gini impurity:

$$
G=1-p_0^2-p_1^2=2p_1(1-p_1).
$$

เมื่อ binary classes เท่ากัน Gini สูงสุด 0.5 และเมื่อมี class เดียว Gini เป็นศูนย์ สูตร multiclass จึงไม่ควรถูกอ่านว่าค่าสูงสุดเป็น 1 สำหรับทุกจำนวน class

```python
from sklearn.tree import DecisionTreeClassifier

small_x = np.arange(6).reshape(-1, 1)
small_y = np.array([0, 0, 0, 1, 1, 1])
stump = DecisionTreeClassifier(max_depth=1, random_state=5).fit(small_x, small_y)
parent_gini = 2 * small_y.mean() * (1 - small_y.mean())
print("Parent Gini:", parent_gini)
print("Split threshold:", stump.tree_.threshold[0])
print("Leaf probabilities:", stump.predict_proba([[1], [4]])[:, 1])
```

ตัวอย่างนี้จงใจแบ่งได้สมบูรณ์ ในข้อมูลจริงการเพิ่มความลึกจนจำทุกแถวได้มักทำให้แต่ละใบมีตัวอย่างน้อย `max_depth` และ `min_samples_leaf` จึงเป็น [hyperparameters](glossary.html#hyperparameter) ที่ควบคุมความละเอียดของการแบ่ง ไม่ควรเลือกจากคะแนนชุดฝึกเพียงอย่างเดียว

## เปรียบเทียบแบบจำลองสี่ตระกูล

| โมเดล | เรียนรู้อะไร | สิ่งที่ต้องระวังในตัวอย่างนี้ |
|---|---|---|
| Logistic | คะแนนเชิงเส้นบน log-odds | สเกล feature และรูปความสัมพันธ์ |
| Tree | กฎแบ่ง feature space | ต้นไม้ลึกอาจจำ noise |
| Forest | เฉลี่ยหลายต้นที่ใช้การสุ่มข้อมูลและ feature | ต้นไม้หลายต้นยังอาจผิดในทิศเดียวกัน |
| Boosting | เพิ่มต้นไม้ทีละต้นเพื่อลด loss ที่เหลือ | learning rate และจำนวนต้นควรเลือกจาก validation |

Random forest ทำต้นไม้หลายต้นโดยสุ่มข้อมูลแบบ bootstrap และสุ่ม feature ที่ให้พิจารณาในจุดแบ่ง ส่วน gradient boosting เพิ่มแบบจำลองตามทิศทางที่ลด loss การเฉลี่ย probability ของโมเดลหลายตัวเฉย ๆ จึงไม่ใช่ขั้นตอน boosting รายละเอียดการทำงานอ้างอิง [scikit-learn ensemble documentation](https://scikit-learn.org/1.6/modules/ensemble.html)

เราใช้ `Pipeline` ให้ StandardScaler เรียนค่าเฉลี่ยและ SD จากชุดฝึกของแต่ละรอบเท่านั้น `C` ใน LogisticRegression เป็น inverse regularization strength: ค่าเล็กลงลงโทษ coefficients มากขึ้น ต่างจากพารามิเตอร์ penalty ที่ยิ่งใหญ่ยิ่งลงโทษมาก

```python
from sklearn.base import clone
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

candidates = {
    "Logistic": make_pipeline(StandardScaler(), LogisticRegression(C=1, max_iter=2000)),
    "Tree": DecisionTreeClassifier(max_depth=3, min_samples_leaf=12, random_state=5),
    "Forest": RandomForestClassifier(n_estimators=60, max_depth=3, min_samples_leaf=8,
                                     random_state=5, n_jobs=1),
    "Boosting": GradientBoostingClassifier(n_estimators=40, learning_rate=0.05,
                                           max_depth=1, random_state=5),
}
print("Candidates:", ", ".join(candidates))
```

ตั้งค่าทั้งสี่ชุดก่อนดูผล ตัวอย่างนี้เปรียบเทียบโมเดลสี่ชุดที่ระบุไว้ ไม่ได้ค้น hyperparameters ทุกค่าหรืออ้างว่าเป็นค่าที่ดีที่สุดของแต่ละตระกูล `clone` ในขั้นต่อไปสร้าง estimator ใหม่ที่มี settings เดิม แต่ไม่มีค่าที่เรียนจากรอบก่อนติดมาด้วย

## Validation สามช่วง โดยไม่สลับเวลา

เริ่มฝึกที่ cutoff 120, 140 และ 160 แล้วทดสอบช่วงถัดไป แถวฝึกต้องมี `label_available <= cutoff` ส่วนผล validation ทั้งหมดต้องประกาศแล้วก่อนเลือกโมเดลที่ cutoff 180 จึงจบช่วงสุดท้ายที่ origin 177 ซึ่ง label พร้อมที่เดือน 180

| รอบ | Cutoff ที่ฝึก | Origin ล่าสุดที่ใช้ฝึก | Origin ที่ประเมิน |
|---|---:|---:|---|
| 1 | 120 | 117 | 120–139 |
| 2 | 140 | 137 | 140–159 |
| 3 | 160 | 157 | 160–177 |

ในแต่ละช่วง validation เราตรึงโมเดลที่ฝึกตอนต้นช่วงไว้ และป้อน feature ของแต่ละเดือนเมื่อถึงเดือนนั้น รอบถัดไปอาจใช้ label ของเดือนที่เคยเป็น validation ได้เมื่อประกาศแล้ว นี่คือการจำลองการปรับแบบจำลองตามลำดับเวลา

```python
from sklearn.metrics import brier_score_loss

folds = [(120, 140), (140, 160), (160, 178)]
validation_rows = []
for name, estimator in candidates.items():
    for cutoff, end in folds:
        training = data[data.label_available <= cutoff]
        validation = data[(data.origin >= cutoff) & (data.origin < end)]
        model = clone(estimator).fit(training[features], training.target)
        probability = model.predict_proba(validation[features])[:, 1]
        validation_rows.append({"model": name, "cutoff": cutoff, "n": len(validation),
                                "brier": brier_score_loss(validation.target, probability)})
validation_scores = pd.DataFrame(validation_rows)
print(validation_scores.round(6).to_string(index=False))
```

เลือกจาก Brier ที่ถ่วงตามจำนวนตัวอย่าง เพราะช่วงสุดท้ายมี 18 แถว ต่างจากสองช่วงแรกที่มี 20 แถว การเอาค่าเฉลี่ยสามช่วงแบบน้ำหนักเท่ากันตอบอีกคำถามหนึ่ง คือให้ทุกช่วงมีความสำคัญเท่ากันไม่ว่ามีตัวอย่างเท่าไร

```python
cv_scores = validation_scores.groupby("model").apply(
    lambda group: np.average(group.brier, weights=group.n), include_groups=False
).sort_values()
selected_name = cv_scores.index[0]
selected_estimator = candidates[selected_name]
print(cv_scores.round(6).to_string())
print("Selected before final evaluation:", selected_name)
```

ด้วย seed นี้ Logistic ได้ Brier ประมาณ 0.200269 และ Boosting ประมาณ 0.200465 ต่างกันน้อยมาก เราใช้กฎเลือกค่าต่ำสุดที่ตั้งไว้จึงได้ Logistic ความต่างระดับนี้ไม่พอยืนยันว่าตระกูลหนึ่งเหนือกว่าอีกตระกูลในตลาดจริง และไม่ได้เปลี่ยน seed เพื่อให้โมเดลที่ซับซ้อนชนะ

## ตรึงกระบวนการ แล้วประเมินเดือน 180–238

สิ่งที่ตรึงคือ features, ชนิดโมเดล, hyperparameters, กฎฝึกใหม่ และวิธีประเมิน เราฝึกใหม่ทุกเดือนโดยเพิ่ม label เก่าที่เพิ่งประกาศได้ จึงเป็นการทดสอบแบบเดินหน้า หรือ prequential evaluation ไม่ใช่โมเดลตัวเดิมที่ตรึง coefficients ตลอดช่วง test

ผลจริงของเดือนทดสอบก่อนหน้าอาจเข้าชุดฝึกในเดือนหลังได้ตามกฎที่ตั้งไว้ สิ่งที่ห้ามคือใช้คำตอบที่ยังไม่ประกาศ หรือเปลี่ยนขั้นตอนเพราะเห็นผลช่วงทดสอบแล้ว ทุกคำพยากรณ์ถูกบันทึกก่อนนำไปจับคู่กับคำตอบของแถวนั้น

```python
def rolling_predict(source, estimator, start=180, end=239):
    records = []
    for t in range(start, end):
        training = source[source.label_available <= t]
        now = source[source.origin == t]
        model = clone(estimator).fit(training[features], training.target)
        probability = model.predict_proba(now[features])[0, 1]
        records.append((t, probability, training.target.mean()))
    return pd.DataFrame(records, columns=["origin", "p", "baseline"])

forecast = rolling_predict(data, selected_estimator)
actual = data.set_index("origin").loc[forecast.origin, "target"].to_numpy()
print(forecast.head().round(6).to_string(index=False))
print("Evaluation months:", len(forecast), "Events:", int(actual.sum()))
```

`baseline` เป็นอัตราเกิดเหตุการณ์ในข้อมูลฝึกที่พร้อมใช้ ณ เดือนนั้น จึงไม่ใช่อัตราที่คำนวณจาก test ทั้งช่วงย้อนหลัง baseline นี้ออก probability ที่มีเหตุผลเปรียบเทียบได้ แม้ไม่ได้ใช้ feature เพื่อแยกเดือน

<figure class="lesson-figure">
<picture>
<source media="(max-width: 520px)" srcset="assets/charts/ml-event-probabilities-mobile.svg">
<img src="assets/charts/ml-event-probabilities.svg" alt="Probability จาก Logistic และอัตราในชุดฝึก เทียบกับเหตุการณ์จริงของข้อมูลจำลอง" loading="lazy" width="720" height="560">
</picture>
<figcaption>ข้อมูลจำลอง seed 501 เส้นม่วงและเส้นประออกก่อนรู้ label ของเดือนถัดไป จุดสีเทาที่ 1 คือเกิดเหตุการณ์ ส่วนที่ 0 คือไม่เกิด probability จึงไม่จำเป็นต้องเท่ากับ label ในแต่ละเดือน และไม่ใช่โอกาสถดถอยจากข้อมูลเศรษฐกิจจริง</figcaption>
</figure>

## ตรวจ Probability และการเตือนคนละส่วน

```python
from sklearn.metrics import log_loss, roc_auc_score, average_precision_score
from sklearn.metrics import confusion_matrix, matthews_corrcoef

prediction_metrics = pd.Series({
    "model_brier": brier_score_loss(actual, forecast.p),
    "baseline_brier": brier_score_loss(actual, forecast.baseline),
    "log_loss": log_loss(actual, forecast.p, labels=[0, 1]),
    "roc_auc": roc_auc_score(actual, forecast.p),
    "average_precision": average_precision_score(actual, forecast.p),
    "accuracy_at_0.5": np.mean((forecast.p >= 0.5) == actual),
    "mcc_at_0.5": matthews_corrcoef(actual, forecast.p >= 0.5),
})
final_confusion = confusion_matrix(actual, forecast.p >= 0.5, labels=[0, 1])
print(prediction_metrics.round(6).to_string())
print("Rows=actual [0,1], columns=predicted [0,1]:")
print(final_confusion)
```

ได้ Brier ประมาณ 0.177658 เทียบ baseline 0.183959 ขณะที่ confusion matrix เป็น `[[44, 1], [14, 0]]` คือพลาดเหตุการณ์จริงทั้ง 14 เดือนเมื่อใช้ threshold 0.5 แม้ probability score ดีกว่า baseline เล็กน้อย และ AUC ประมาณ 0.652381 การจัดอันดับพอมีข้อมูลจึงไม่เท่ากับการเตือนที่ใช้การได้

สำหรับ threshold 0.5 baseline ที่ทายว่าไม่เกิดเสมอตอบถูก $45/59\approx76.27\%$ มากกว่าโมเดลที่ตอบถูก $44/59\approx74.58\%$ อีกด้วย ควรอ่านผลที่ไม่สวยนี้ตามที่ได้ หากวัตถุประสงค์คือเตือนเหตุการณ์ เราต้องออกแบบ loss และเลือก threshold บน validation ให้สอดคล้องตั้งแต่ต้น ไม่ใช้ผล test นี้ปรับ threshold แล้วรายงานเป็นผลที่ไม่เคยเห็น

## ทดสอบว่าอนาคตยังเปลี่ยนอดีตไม่ได้

ลองแก้ feature ทุกแถวตั้งแต่เดือน 210 และแก้ target ที่จะประกาศตั้งแต่เดือน 210 จากนั้นพยากรณ์ใหม่เฉพาะเดือน 180–209 ผลก่อน cutoff ต้องเหมือนเดิมทุกเดือน

```python
perturbed = data.copy()
perturbed.loc[perturbed.origin >= 210, features] += 100
late_labels = perturbed.label_available >= 210
perturbed.loc[late_labels, "target"] = 1 - perturbed.loc[late_labels, "target"]
earlier_forecast = rolling_predict(perturbed, selected_estimator, end=210)
original_earlier = forecast[forecast.origin < 210]
future_invariance = np.allclose(earlier_forecast.p, original_earlier.p)
print("Predictions before month 210 unchanged:", future_invariance)
```

ผลควรเป็น `True` การตรวจนี้จับข้อผิดพลาดบางประเภท เช่น fit scaler จากทุกแถว หรือดึง label อนาคตมาฝึก แต่ยังพิสูจน์ไม่ได้ว่าข้อมูลจริงใช้ได้ ณ วันนั้น หากต้นทางให้ข้อมูลฉบับแก้ไขย้อนหลังมาแล้ว การเปลี่ยนไฟล์ภายหลังเพียงแบบเดียวก็อาจไม่เปิดเผยปัญหานั้น

## เมื่อเปลี่ยนจากข้อมูลจำลองเป็นข้อมูลเศรษฐกิจ

ต้องกำหนดปฏิทิน feature และ label ก่อน เลือก vintage ที่รู้จริงในวันตัดสินใจ แล้วแปลงข้อมูลให้เหมาะกับหน่วย เช่น growth rate หรือ first difference การใช้ difference หรือ log ไม่ได้ยืนยัน stationarity โดยอัตโนมัติ และ log ใช้กับค่าที่เป็นบวกเท่านั้น

การเติมค่าขาดหายต้องใช้กฎที่ทำได้ในวันนั้น Forward fill ใช้ค่าเดิมได้เมื่อค่าเดิมเคยเผยแพร่แล้ว แต่ไม่ได้เปลี่ยนข้อมูลที่ยังไม่ออกให้กลายเป็นข้อมูลใหม่ การคัดทิ้ง feature จากจำนวน missing ตลอดช่วงประวัติรวมอนาคตก็อาจทำให้กระบวนการเลือก feature มองอนาคต ควรเลือกด้วยข้อมูลฝึกและตรวจว่าช่วงทดสอบใช้คอลัมน์เดิมได้อย่างไร

ท้ายที่สุดต้องรายงาน horizon, ช่วงฝึก, ช่วงทดสอบ, จำนวนเหตุการณ์, ขั้นตอนที่เลือกจาก validation และข้อจำกัดของ label แยกให้เห็น ความสำเร็จบนข้อมูลจำลองนี้พิสูจน์ได้เพียงว่าโค้ดทำตามการทดลองที่ตั้งไว้ ยังไม่พิสูจน์ว่าพยากรณ์ Recession จริงได้

## แบบฝึกหัด

<details><summary>1. ทำไมต้อง lag Indicator แต่ไม่ lag Market ในตัวอย่าง?</summary>
<p>เป็นเพราะสมมติฐานเวลาเผยแพร่ที่กำหนดไว้ Indicator เดือน t ออกเดือน t+1 ส่วน Market เดือน t รู้ก่อนตัดสินใจสิ้นเดือน t ถ้าเปลี่ยนเวลาส่งคำสั่งซื้อขายเป็นก่อนตลาดปิด ต้องเปลี่ยนชุดข้อมูลที่ใช้ได้ด้วย</p>
</details>

<details><summary>2. ที่ origin 181 ใช้ target ของ origin 180 ฝึกได้หรือไม่?</summary>
<p>ไม่ได้ target ของ origin 180 เป็นเหตุการณ์เดือน 181 และประกาศเดือน 183 จึงยังไม่พร้อมที่เดือน 181 ในตอนนั้นแถวฝึกล่าสุดเริ่ม origin 178</p>
</details>

<details><summary>3. ทำไมให้ validation สุดท้ายจบที่ origin 177?</summary>
<p>เราจะเลือกโมเดลที่ cutoff 180 และ label ของ origin 177 พร้อมเดือน 180 พอดี หากรวม origin 178 ต้องรอคำตอบถึงเดือน 181 ซึ่งเลยเวลาที่กำหนดสำหรับการเลือกโมเดล</p>
</details>

<details><summary>4. Random forest กับ Gradient boosting ต่างกันตรงไหน?</summary>
<p>Forest รวมต้นไม้ที่สร้างจากการสุ่มข้อมูลและ feature โดยแต่ละต้นไม่ต้องรอแก้ข้อผิดพลาดของต้นก่อนหน้า Boosting เพิ่มตัวเรียนรู้ตามลำดับเพื่อปรับคะแนนและลด loss ที่เหลือ ทั้งสองยังต้องทดสอบนอกตัวอย่าง</p>
</details>

<details><summary>5. โมเดลมี Brier ดีกว่า baseline แต่ recall เป็นศูนย์ได้หรือไม่?</summary>
<p>ได้ probability อาจจัดความเสี่ยงได้บางส่วน แต่ยังไม่สูงพอข้าม threshold ที่เลือก คะแนนของ probability กับกฎเตือนเป็นคนละส่วน ตัวอย่างบทนี้เกิดกรณีนี้จริง</p>
</details>

<details><summary>6. ใช้ label ของเดือนทดสอบเก่าฝึกใหม่ในเดือนหลัง ทำให้ test ใช้ไม่ได้เสมอหรือไม่?</summary>
<p>ไม่เสมอไป ถ้ากำหนดขั้นตอนการฝึกใหม่ไว้ก่อน ทราบ label นั้นจริงแล้ว และบันทึกคำพยากรณ์แต่ละเดือนก่อนเห็นผลของแถวนั้น จะเป็นการประเมินกระบวนการเรียนรู้แบบเดินหน้า ต้องเรียกและอธิบายให้ตรง ไม่อ้างว่าเป็นโมเดลที่ตรึง coefficients ตลอดช่วง</p>
</details>

<details><summary>7. เพิ่มต้นไม้เป็นพันต้นแล้วคะแนนชุดฝึกดีขึ้น ควรเลือกทันทีหรือไม่?</summary>
<p>ไม่ควร ต้องเปรียบเทียบภายใน validation ตามเวลา พร้อมต้นทุนคำนวณและความเสถียร หากนำค่าที่ทดลองเพิ่มมาดู final test ซ้ำ ชุดนั้นจะกลายเป็นส่วนหนึ่งของการเลือกแบบจำลอง</p>
</details>

อ่านต่อ [เลือก Feature และตรวจความเสถียร](feature-selection.html) เพื่อดูว่าความสัมพันธ์ที่โมเดลพบขึ้นกับคอลัมน์ ช่วงเวลา และเกณฑ์เลือกอย่างไร
