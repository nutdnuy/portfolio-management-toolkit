---
title: "ตรวจ Factor Model ตามเวลา: เลือกค่า Penalty ก่อนดู Test"
description: "แยก development และ final test เลือก hyperparameter ด้วย expanding windows และตรวจการรั่วไหลของข้อมูล"
---

# ตรวจ Factor Model ตามเวลา: เลือกค่า Penalty ก่อนดู Test

<p class="lead">เมื่อมี Ridge, Lasso และ Elastic Net แล้ว เรายังต้องเลือกว่าจะใช้วิธีใดและตั้ง penalty เท่าไร การเลือกจากข้อมูลที่ใช้ฝึกอย่างเดียวจะให้ประโยชน์กับโมเดลที่ fit ข้อมูลนั้นได้มาก จึงต้องกันข้อมูลสำหรับเปรียบเทียบโมเดลและกันอีกช่วงสำหรับตรวจผลหลังเลือกเสร็จ</p>

บทนี้สร้างข้อมูลสมมติ 120 เดือน ใช้ 96 เดือนแรกเลือกโมเดลด้วยการเดินเวลาไปข้างหน้า แล้วเปิดผล 24 เดือนสุดท้ายเพียงหลังตัดสินใจแล้ว ทุกโมเดลได้เห็นช่วงข้อมูล ปัจจัย และเป้าหมายเดียวกัน เราจะอ่านทั้งขนาด error และ loading ที่ได้ โดยไม่แปลงคะแนนการอธิบายผลตอบแทนให้เป็นคำแนะนำซื้อขาย

<span id="validation-task-definition"></span>

## ระบุสิ่งที่เราทดสอบให้ตรงกับข้อมูล

เราจะประมาณความสัมพันธ์ $y_t=a+F_t^\mathsf T\beta+e_t$ ของผลตอบแทนกองทุนกับผลตอบแทนปัจจัยในเดือนเดียวกัน Training data อยู่ก่อน validation และ test ตามปฏิทิน แต่ตอนคำนวณ fitted value ของเดือนทดสอบ เรายังใส่ผลตอบแทนปัจจัยที่เกิดจริงในเดือนนั้น

ผลที่วัดจึงเป็นความสามารถของสมการในการอธิบายความสัมพันธ์ในช่วงใหม่แบบมีปัจจัยให้แล้ว หากต้องการทำนายก่อนเดือนเริ่ม ต้องมีตัวแปรที่รู้ ณ ตอนนั้น หรือพยากรณ์ปัจจัยก่อนอีกขั้น การเปลี่ยนชื่อ `.predict` ไม่ได้ทำให้ input ในอนาคตทราบได้ล่วงหน้า

คำที่ใช้ในบทนี้มีสามชุด:

| ชุดข้อมูล | ใช้ทำอะไร | สิ่งที่ยอมให้เรียนรู้จากชุดนี้ |
|---|---|---|
| Training fold | ฝึกหนึ่งโมเดลในการเปรียบเทียบแต่ละรอบ | ค่าเฉลี่ย/SD สำหรับปรับสเกล, intercept, loading |
| Validation fold | เปรียบเทียบตัวเลือกภายใน development data | เลือกชนิดโมเดลและ hyperparameter |
| Final test | ประเมินหลังเลือกทุกอย่างแล้ว | รายงานผล ไม่ย้อนกลับไปเลือกผู้ชนะใหม่ |

Development data หมายถึงข้อมูลทั้งหมดที่ยอมใช้สร้างและเลือกโมเดล ซึ่งในบทนี้คือ 96 เดือนแรก และถูกแบ่งเป็น training/validation ย่อยหลายรอบ ส่วน test 24 เดือนสุดท้ายไม่เข้าไปอยู่ในการแบ่งย่อยนั้น

```python
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.metrics import mean_squared_error, r2_score

np.set_printoptions(precision=6, suppress=True)
```

`clone` สร้างตัวประมาณใหม่ที่มีค่าตั้งเหมือนเดิม แต่ยังไม่มีผลการฝึก `Pipeline` เชื่อมขั้นตอนปรับสเกลและโมเดล `TimeSeriesSplit` สร้างตำแหน่งแถวสำหรับเดินเวลา ส่วน `GridSearchCV` ลองค่าตั้งที่ระบุและรวบรวมคะแนน validation ใช้ scikit-learn 1.6.1 ตรวจตัวอย่างทั้งหน้า ซึ่งรันจาก namespace ว่างได้

<span id="validation-synthetic-data"></span>

## สร้างข้อมูลและกัน Test ก่อน

ปัจจัยหกตัวใช้ทศนิยมต่อเดือนทั้งหมด Equity proxy เกือบซ้ำกับ Equity และ Rates mirror เกือบเป็นค่าติดลบของ Rates เราใช้ชื่อเพื่ออ่านตารางง่าย แต่ทุกแถวเป็นข้อมูลจำลองจากสูตร ไม่ใช่ข้อมูลตลาดจริงระหว่างปีที่แสดงบน index

```python
validation_rng = np.random.default_rng(20261004)
validation_latent = validation_rng.normal(size=(120, 6))
validation_dates = pd.period_range("2015-01", periods=120, freq="M")
validation_X = pd.DataFrame({
    "Equity": 0.004 + 0.04 * validation_latent[:, 0],
    "Equity proxy": 0.004 + 0.04 * (validation_latent[:, 0] + 0.1 * validation_latent[:, 1]),
    "Rates": 0.001 + 0.02 * validation_latent[:, 2],
    "Rates mirror": -0.001 + 0.02 * (-validation_latent[:, 2] + 0.1 * validation_latent[:, 3]),
    "FX": 0.02 * validation_latent[:, 4],
    "Noise proxy": 0.03 * validation_latent[:, 5],
}, index=validation_dates)
validation_true_beta = np.array([0.7, 0, -0.25, 0, 0.1, 0])
validation_y = pd.Series(
    0.001 + validation_X.to_numpy() @ validation_true_beta + validation_rng.normal(0, 0.012, 120),
    index=validation_dates, name="Fund",
)
print("Observations:", len(validation_X), "Factors:", validation_X.shape[1])
print("Period:", validation_X.index[0], "to", validation_X.index[-1])
```

`normal(size=(120, 6))` สร้างเลขสุ่ม Normal 120 แถว หกคอลัมน์ `.iloc` ที่จะใช้ต่อไปเลือกแถวตามตำแหน่ง ส่วน `PeriodIndex` ช่วยติดชื่อเดือนให้ตรวจเวลาได้ง่าย เรากำหนด coefficient จริง `[0.7, 0, -0.25, 0, 0.1, 0]` ไว้เพื่อทราบโครงสร้างของการจำลอง แต่ตอนเลือกโมเดลจะไม่ส่งค่าจริงเหล่านี้เข้าโปรแกรม

loading จริงคงที่ทั้ง 120 เดือนในตัวอย่างนี้ ดังนั้นความต่างของค่าประมาณระหว่างช่วงเกิดได้แม้ยังไม่มีการเปลี่ยนภาวะตลาด เราเพิ่ม residual ที่มี SD 0.012 หรือ 1.2% ต่อเดือน ซึ่งทำให้มีข้อมูลส่วนที่ปัจจัยไม่อธิบาย

การจำลอง Normal ใช้ศึกษาการประมาณสมการเท่านั้น ไม่ได้ใช้ทบเป็นราคาหรืออ้างว่า tails ของผลตอบแทนตลาดเป็น Normal

```python
development_X, final_X = validation_X.iloc[:96], validation_X.iloc[96:]
development_y, final_y = validation_y.iloc[:96], validation_y.iloc[96:]
print("Development:", development_X.index[0], "to", development_X.index[-1], len(development_X))
print("Final test:", final_X.index[0], "to", final_X.index[-1], len(final_X))
print("Dates aligned:", validation_X.index.equals(validation_y.index))
print("Finite data:", np.isfinite(validation_X.to_numpy()).all() and np.isfinite(validation_y).all())
```

`[:96]` เลือกตำแหน่ง 0 ถึง 95 หรือ 96 เดือนแรก ส่วน `[96:]` เริ่มที่แถวตำแหน่ง 96 จนจบ ผลได้ development มกราคม 2015 ถึงธันวาคม 2022 และ final test มกราคม 2023 ถึงธันวาคม 2024 จำนวน 24 เดือน

`.index.equals` ตรวจว่าชื่อเดือนของ X และ y ตรงกันทั้งลำดับ `np.isfinite` ตรวจว่าตัวเลขไม่มี NaN หรือ infinity ก่อนฝึก ในงานจริงยังต้องตรวจ index ซ้ำ เดือนที่หาย หน่วย สกุลเงิน และวันที่ข้อมูลเผยแพร่ การเรียงตามเดือนอย่างเดียวไม่ป้องกันการใช้ตัวเลขเศรษฐกิจที่ถูกแก้ไขภายหลังย้อนหลังไปในอดีต

อย่าเติมผลตอบแทนที่หายด้วยค่าของเดือนถัดไป และอย่าทำ forward fill จนกลายเป็นผลตอบแทนที่สร้างขึ้นเอง หากต้อง impute ตัวแปรชนิดอื่น ค่าที่ใช้ impute ต้องเรียนจาก training fold เท่านั้นและสอดคล้องกับเวลาที่รู้ข้อมูล

<span id="expanding-validation-folds"></span>

## แบ่ง Validation ให้เดินไปข้างหน้า

ภายใน 96 เดือนแรก เราใช้สามรอบ รอบแรกฝึก 60 เดือนและตรวจ 12 เดือนถัดไป รอบต่อไปขยายช่วงฝึกให้รวมข้อมูลที่เวลาผ่านไปแล้ว จากนั้นตรวจอีก 12 เดือน

```python
validation_splitter = TimeSeriesSplit(n_splits=3, test_size=12)
validation_folds = list(validation_splitter.split(development_X))
for fold, (train_idx, valid_idx) in enumerate(validation_folds, start=1):
    print(
        f"Fold {fold}: train {development_X.index[train_idx[0]]}--{development_X.index[train_idx[-1]]} "
        f"({len(train_idx)} months), validate {development_X.index[valid_idx[0]]}--{development_X.index[valid_idx[-1]]} "
        f"({len(valid_idx)} months)"
    )
```

| รอบ | Training | Validation |
|---|---|---|
| 1 | ม.ค. 2015–ธ.ค. 2019, 60 เดือน | ปี 2020, 12 เดือน |
| 2 | ม.ค. 2015–ธ.ค. 2020, 72 เดือน | ปี 2021, 12 เดือน |
| 3 | ม.ค. 2015–ธ.ค. 2021, 84 เดือน | ปี 2022, 12 เดือน |

แถวที่เคยใช้ validation ในรอบก่อนเข้ามาเป็น training ของรอบหลังได้ เพราะในรอบหลังเวลานั้นผ่านไปแล้ว ส่วนข้อมูล 2023–2024 ยังไม่ถูกแตะ `enumerate(..., start=1)` ช่วยพิมพ์เลขรอบเริ่มจากหนึ่ง และแต่ละคู่ที่ตัวแบ่งคืนมาคืออาร์เรย์ตำแหน่ง training กับ validation

K-fold ทั่วไปแม้ตั้ง `shuffle=False` ก็อาจเอาข้อมูลที่เกิดหลัง validation มาฝึกในบางรอบ เพราะมันใช้กลุ่มอื่นทั้งหมดเป็น training การเลือก splitter ต้องตรงกับคำถามที่ต้องการประเมิน สำหรับการนำโมเดลไปใช้ในช่วงเวลาถัดไป ตัวอย่างนี้จึงบังคับอดีตก่อนอนาคต

เรายังใช้ `gap=0` ซึ่งเป็นค่าเริ่มต้น เพราะหนึ่ง label ครอบคลุมหนึ่งเดือนและไม่มีช่วงผลตอบแทนซ้อนกัน หากเปลี่ยน y เป็นผลตอบแทนล่วงหน้าหลายเดือน หรือข้อมูลมีความล่าช้าในการประกาศ ต้องเว้นหรือจัดช่วงข้อมูลให้ไม่มีข้อมูลจากช่วง validation ปนอยู่ใน label ของ training โดยกำหนดจาก timing ของโจทย์ ไม่ใช่เลือก gap จากตัวเลขที่จำมา

<span id="pipeline-grid-search"></span>

## ให้การปรับสเกลอยู่ภายในแต่ละ Fold

ในทุกการฝึก เราให้ StandardScaler เรียนค่าเฉลี่ยและ SD จาก training ของรอบนั้นก่อน แล้วใช้ค่าที่เก็บไว้แปลง validation การ fit scaler ครั้งเดียวบนข้อมูล 96 เดือนก่อนแบ่ง fold จะทำให้รอบแรกได้ใช้ข้อมูลจากปี 2020–2022 มาตั้งสเกล ทั้งที่ training ของรอบนั้นควรจบปี 2019

เราสร้าง Pipeline ชื่อขั้นตอน `scale` และ `model` แล้วให้ GridSearchCV ฝึก pipeline ใหม่ในแต่ละ fold

```python
validation_candidates = {
    "OLS": (LinearRegression(), {}),
    "Ridge": (Ridge(), {"model__alpha": [0.1, 1.0, 10.0, 100.0]}),
    "Lasso": (Lasso(tol=1e-10, max_iter=100000), {"model__alpha": [0.00005, 0.0002, 0.0005, 0.001, 0.002, 0.005]}),
    "Elastic Net": (ElasticNet(tol=1e-10, max_iter=100000), {
        "model__alpha": [0.00005, 0.0002, 0.0005, 0.001, 0.002, 0.005],
        "model__l1_ratio": [0.2, 0.5, 0.8],
    }),
}
validation_searches = {}
for name, (estimator, grid) in validation_candidates.items():
    pipeline = Pipeline([("scale", StandardScaler()), ("model", estimator)])
    search = GridSearchCV(
        pipeline, grid, cv=validation_folds, scoring="neg_mean_squared_error",
        refit=True, error_score="raise", n_jobs=1,
    )
    search.fit(development_X, development_y)
    validation_searches[name] = search
print("Models fitted:", list(validation_searches))
```

dictionary `validation_candidates` เก็บคู่ระหว่างตัวประมาณกับค่าที่จะลอง OLS มี `{}` เพราะไม่มี penalty ให้เลือก ส่วน `model__alpha` ใช้ขีดล่างสองตัวเพื่อบอกว่าให้ตั้ง `alpha` ของขั้นตอนชื่อ `model` ภายใน Pipeline สำหรับ Elastic Net ยังลอง `model__l1_ratio` อีกสามค่า

ตารางค่าตั้งเหล่านี้เป็นตัวเลือกสำหรับการสาธิต เราไม่ได้ค้นหาไปเรื่อย ๆ หลังเห็น final test และไม่ได้อ้างว่า grid นี้เหมาะกับทุกข้อมูล หากคำตอบที่เลือกอยู่ขอบ grid ต้องพิจารณาขยายช่วงจาก development/validation โดยรักษา final test ไว้

ความหมายของ `alpha` ต่างกันระหว่าง Ridge กับ Lasso ตาม [นิยาม objective](regularized-factor-models.html#ridge-hand-calculation) จึงใช้ grid แยกกัน Ridge ในโค้ดนี้ลองค่า `alpha` ตาม API โดยตรง เมื่อจำนวน training observations เพิ่ม penalty สัมพัทธ์กับ SSE เฉลี่ยจะเปลี่ยนได้ ไม่ได้อ้างว่าทุกรอบมี normalized penalty เท่ากัน

`scoring="neg_mean_squared_error"` ให้คะแนนเป็น MSE ติดลบ เพราะ GridSearchCV เลือกคะแนนที่มากที่สุด เช่น −0.0001 ดีกว่า −0.0002 เราจึงเปลี่ยนเครื่องหมายกลับตอนรายงาน MSE `error_score="raise"` ทำให้หยุดและแจ้งปัญหาถ้า fit ไม่สำเร็จ แทนการกลบไว้ด้วยคะแนนว่าง และ `refit=True` ให้ฝึกค่าตั้งที่ชนะซ้ำบน development ทั้งหมดหลังเลือกแล้ว

<span id="validation-select-before-test"></span>

## เลือกโมเดลจาก Validation

```python
validation_summary = pd.DataFrame([
    {"Model": name, "Validation MSE": -search.best_score_, "Settings": str(search.best_params_)}
    for name, search in validation_searches.items()
]).set_index("Model")
validation_winner = validation_summary["Validation MSE"].idxmin()
selected_pipeline = validation_searches[validation_winner].best_estimator_
print(validation_summary.to_string(float_format=lambda value: f"{value:.8f}"))
print("Selected before final test:", validation_winner)
```

แต่ละค่าตั้งได้ MSE ของ validation สามรอบ เราเฉลี่ย MSE เหล่านั้นก่อนเลือกค่าที่ต่ำที่สุด ทุก fold ยาว 12 เดือนเท่ากัน จึงเท่ากับการรวม squared errors ของทั้ง 36 แถวแล้วหาร 36 ถ้าต้องแสดง RMSE จากคะแนนนี้ให้ถอดรากหลังเฉลี่ย MSE ไม่ใช่เฉลี่ย RMSE แล้วถือว่าเป็นตัวเดียวกัน

ผลจากข้อมูลจำลองนี้เป็นดังนี้:

| โมเดล | Validation MSE ที่ดีที่สุด | ค่าที่เลือก |
|---|---:|---|
| OLS | 0.00011327 | ไม่มี penalty |
| Ridge | 0.00010988 | alpha = 1 |
| Lasso | 0.00011007 | alpha = 0.00005 |
| Elastic Net | 0.00011003 | alpha = 0.0002, l1_ratio = 0.5 |

เราเลือก Ridge ก่อนดู final test แต่ความต่างของคะแนนเล็ก ไม่ควรตีความอันดับนี้เป็นความแน่นอนทางสถิติ การใช้ validation เพื่อเลือกทั้งค่าตั้งและตระกูลโมเดลทำให้คะแนนชนะผ่านการคัดเลือกมาแล้ว จึงยังต้องใช้ final test แยกต่างหาก

ตรวจหนึ่ง fold ว่า scaler ใช้เฉพาะ training 60 เดือน และโมเดลที่ refit แล้วใช้ development 96 เดือน

```python
fold_train, fold_valid = validation_folds[0]
fold_model = clone(selected_pipeline).fit(development_X.iloc[fold_train], development_y.iloc[fold_train])
fold_scaler_mean = fold_model.named_steps["scale"].mean_
fold_manual_mean = development_X.iloc[fold_train].mean().to_numpy()
print("Scaler uses fold training mean:", np.allclose(fold_scaler_mean, fold_manual_mean))
print("Fold training months:", len(fold_train))
print("Refit training months:", selected_pipeline.named_steps["scale"].n_samples_seen_)
```

ผลตรวจค่าเฉลี่ยต้องเป็น `True` และจำนวนเดือนเป็น 60 กับ 96 ตามลำดับ `clone` ไม่คัดลอกผลการฝึกเดิม เมื่อ `.fit` อีกครั้งจึงเรียน scaler และ loading ใหม่จากข้อมูลที่ส่งให้

<span id="factor-final-test"></span>

## เปิด Test หลังเลือกเสร็จ

เรารายงานทุกวิธีที่กำหนดไว้เพื่อดูความไม่แน่นอนของผล แต่คงการเลือก Ridge จาก validation ไว้ การเปลี่ยนผู้ชนะหลังดูตารางนี้จะทำให้ test กลายเป็น validation อีกชุด

```python
validation_test_rows = []
for name, search in validation_searches.items():
    prediction = search.best_estimator_.predict(final_X)
    validation_test_rows.append({
        "Model": name,
        "Final RMSE (pp/month)": 100 * np.sqrt(mean_squared_error(final_y, prediction)),
        "Final R squared": r2_score(final_y, prediction),
    })
validation_test_table = pd.DataFrame(validation_test_rows).set_index("Model")
constant_prediction = np.full(len(final_y), development_y.mean())
print(validation_test_table.round(6))
print(f"Training-mean baseline RMSE: {100 * np.sqrt(mean_squared_error(final_y, constant_prediction)):.6f} pp/month")
print("Selection remains:", validation_winner)
```

| โมเดล | Final RMSE, จุดเปอร์เซ็นต์ต่อเดือน | Final R² |
|---|---:|---:|
| OLS | 1.052372 | 0.881214 |
| Ridge ที่เลือกไว้ | 1.073553 | 0.876384 |
| Lasso | 1.057553 | 0.880041 |
| Elastic Net | 1.059014 | 0.879709 |

Ridge ชนะ validation แต่ OLS มี test error ต่ำกว่าเล็กน้อยในข้อมูลช่วงสุดท้ายนี้ ส่วน baseline ที่ใส่เพียงค่าเฉลี่ย y จาก training ทุกเดือนมี RMSE ประมาณ 3.054034 จุดเปอร์เซ็นต์ เราใช้ค่าเฉลี่ยจาก training เพราะมันเป็นค่าที่มีอยู่ก่อน test เริ่ม

`r2_score` ใช้ค่าเฉลี่ยของ y ในชุดที่ประเมินเป็นตัวหารตามนิยาม R² จึงเป็นตัววัดความพอดีเชิงสถิติของชุดนั้น ไม่ใช่พอร์ต benchmark ที่ซื้อขายได้ และนอกชุดฝึก R² อาจติดลบได้ การได้ R² สูงในที่นี้ยังอาศัยการป้อนผลตอบแทนปัจจัยของเดือนเดียวกัน ไม่ใช่กำไรจากการพยากรณ์ล่วงหน้า

<span id="validation-read-loadings"></span>

## อ่าน Loading ในหน่วยเดิมและดูความไม่นิ่ง

Pipeline ประมาณ coefficient บนปัจจัยที่ปรับสเกลแล้ว ถ้าต้องใช้กับผลตอบแทนทศนิยมเดิม ต้องหาร coefficient ด้วย SD ของ training และปรับ intercept ด้วยค่าเฉลี่ย training

```python
selected_scaler = selected_pipeline.named_steps["scale"]
selected_model = selected_pipeline.named_steps["model"]
selected_beta = selected_model.coef_ / selected_scaler.scale_
selected_alpha = selected_model.intercept_ - selected_scaler.mean_ @ selected_beta
selected_direct = selected_alpha + final_X.to_numpy() @ selected_beta
print(pd.Series(selected_beta, index=development_X.columns, name="Original-unit loading").round(6))
print(f"Monthly intercept: {selected_alpha:.6f}")
print("Direct formula matches pipeline:", np.allclose(selected_direct, selected_pipeline.predict(final_X)))
```

ได้ loading ของ Equity ประมาณ 0.426577 และ Equity proxy ประมาณ 0.227318 ขณะที่สูตรสร้างข้อมูลใช้ Equity 0.7 และ proxy ศูนย์ ตัวประมาณแบ่ง coefficient ระหว่างตัวแทนที่สัมพันธ์กันสูง จึงอาจอธิบาย y ได้ใกล้เคียงแม้ไม่ได้คืน coefficient จริงทีละตัว ส่วน loading ของ Noise proxy ไม่เป็นศูนย์พอดี ซึ่งสอดคล้องกับ Ridge ที่ไม่ได้ใช้ penalty แบบคัดตัวแปรให้เป็นศูนย์

เราตรวจสมการที่แปลงกลับด้วย `selected_alpha + X @ selected_beta` เทียบกับ Pipeline ผล `True` ยืนยันความสอดคล้องทางหน่วยภายในตัวอย่าง ไม่ได้ยืนยันว่า loading ที่ประมาณตรงกับเศรษฐกิจจริง

ลองใช้ค่าตั้งที่เลือกไว้ fit บนช่วงข้อมูลที่ยาวขึ้น เพื่อดูความไวของ coefficient ต่อข้อมูล

```python
stability_rows = []
for end in [60, 72, 84, 96]:
    model = clone(selected_pipeline).fit(development_X.iloc[:end], development_y.iloc[:end])
    scaler = model.named_steps["scale"]
    beta = model.named_steps["model"].coef_ / scaler.scale_
    stability_rows.append([end, *beta])
validation_stability = pd.DataFrame(stability_rows, columns=["Training months", *development_X.columns])
print(validation_stability.round(4).to_string(index=False))
```

ตัวอย่างเช่น loading ของ Rates เคลื่อนจากประมาณ −0.0864 เมื่อใช้ 60 เดือน เป็น −0.2290 เมื่อใช้ 96 เดือน ทั้งที่ loading จริงในสูตรจำลองคงที่ การเปลี่ยนค่าประมาณจึงอาจมาจาก noise และการแยกบทบาทของปัจจัยที่ซ้ำกันด้วย ไม่ใช่หลักฐานยืนยัน regime change โดยตัวมันเอง

ตารางนี้เป็นการตรวจความไวภายหลัง โดยใช้ hyperparameter ที่เลือกจาก development 96 เดือนแล้ว ไม่ใช่บันทึกคำตัดสินที่เคยทำได้จริง ณ เดือนที่ 60 หากต้องการจำลองการตัดสินใจย้อนหลังเต็มรูปแบบ ต้องเลือก hyperparameter ใหม่จากข้อมูลก่อนแต่ละวันตัดสินใจด้วย

<span id="validation-factor-scenario"></span>

## ใช้สมมติฐาน Factor Return และตรวจขอบเขตข้อมูล

สมมติให้ expected monthly factor returns เป็น Equity 0.6%, Equity proxy 0.6%, Rates 0.2%, Rates mirror −0.1% และสองปัจจัยที่เหลือศูนย์ ทั้งหมดเป็นข้อสมมติสำหรับคำนวณ ไม่มีการนำผลตลาดปัจจุบันมาใช้

```python
validation_scenario = pd.DataFrame(
    [[0.006, 0.006, 0.002, -0.001, 0.0, 0.0]],
    columns=development_X.columns,
)
validation_monthly_estimate = selected_pipeline.predict(validation_scenario)[0]
print(f"Conditional monthly estimate: {100 * validation_monthly_estimate:.6f}%")
print(f"Arithmetic annualized estimate: {100 * 12 * validation_monthly_estimate:.6f}%")
```

ได้ค่าประมาณ 0.286687% ต่อเดือน และ 3.440240% ต่อปีแบบคูณ 12 ตัวเลขนี้มีเงื่อนไขทั้งต่อ loading/intercept ที่ประมาณและ expected factor returns ที่สมมติ ไม่ใช่ realized return หรือ CAGR หากใช้ค่าที่ป้อนเป็นผลตอบแทนทศนิยมอยู่แล้ว ไม่ต้องหาร 100 ซ้ำ

เป็นการตรวจขั้นตอนอีกแบบหนึ่ง ลองเปลี่ยน Equity ในแถว final test อย่างรุนแรง แล้ว fit ใหม่จาก development เดิม coefficient ที่ฝึกควรไม่เปลี่ยน

```python
validation_probe = validation_X.copy()
validation_probe.iloc[96:, 0] += 0.50
probe_pipeline = clone(selected_pipeline).fit(validation_probe.iloc[:96], development_y)
probe_coefficient_difference = np.max(np.abs(
    probe_pipeline.named_steps["model"].coef_ - selected_model.coef_
))
print("Changed future rows:", len(validation_probe.iloc[96:]))
print(f"Change in fitted standardized coefficients: {probe_coefficient_difference:.12f}")
```

ค่าต่างของ standardized coefficients ต้องเป็นศูนย์ภายในความคลาดเคลื่อนของเครื่อง เพราะทั้งสองครั้งส่ง 96 แถวเดิมเข้า `.fit` ผลนี้ตรวจเฉพาะขอบเขตการ refit ที่แสดงไว้ ไม่ได้แทนการตรวจทุกขั้นตอนของงานจริง หากการคัดปัจจัย การทำความสะอาด หรือการปรับสเกลก่อนหน้านี้เคยใช้อนาคต ข้อมูลก็ยังรั่วได้

เมื่อนำไปใช้กับข้อมูลจริง ควรบันทึกวันที่ซึ่งแต่ละ feature พร้อมใช้งาน เลือกช่วง train/validation/test ก่อนทดลอง และบันทึกสิ่งที่เปลี่ยนหลังดูคะแนน ความล่าช้าของข้อมูล การแก้ไขข้อมูลย้อนหลัง และการลองหลายแบบล้วนเปลี่ยนความหมายของผลทดสอบได้

<span id="factor-validation-practice"></span>

## แบบฝึกหัด

<details><summary>1. ทำไมการ fit StandardScaler บนข้อมูลทั้งหมดก่อนแบ่งชุดจึงมีปัญหา</summary>

ค่าเฉลี่ยและ SD จะรวมข้อมูลจากช่วงที่กำลังใช้ทดสอบแล้ว ข้อมูลนั้นจึงมีส่วนในการสร้างโมเดลก่อนประเมิน ควรให้ scaler อยู่ใน Pipeline ที่ fit เฉพาะ training ของแต่ละรอบ

</details>

<details><summary>2. ในรอบแรกของตัวอย่าง มี training กี่เดือน และ validation อยู่ปีใด</summary>

Training 60 เดือนตั้งแต่ 2015–2019 และ validation 12 เดือนของปี 2020 รอบแรกต้องไม่ใช้ปี 2021 หรือ 2022 ฝึก scaler หรือ loading

</details>

<details><summary>3. GridSearchCV ให้คะแนน −0.00012 กับ −0.00010 ควรเลือกค่าใดเมื่อ scoring เป็น neg_mean_squared_error</summary>

เลือก −0.00010 เพราะคะแนนมากกว่า และแปลกลับเป็น MSE 0.00010 ที่ต่ำกว่า

</details>

<details><summary>4. คำสั่ง refit=True ใช้ final test มาฝึกด้วยหรือไม่</summary>

ใช้เฉพาะข้อมูลที่ส่งเข้า `search.fit` ซึ่งบทนี้คือ development 96 เดือน ไม่ได้ดึง test เข้ามาเอง หากส่งข้อมูลทั้งหมดเข้า `.fit` ตั้งแต่แรกจึงจะรวม test โดยความผิดพลาดของผู้ใช้

</details>

<details><summary>5. Ridge แพ้ OLS บน final test ควรเปลี่ยนชื่อโมเดลที่เลือกเป็น OLS แล้วอ้างคะแนนเดิมหรือไม่</summary>

หากเปลี่ยนจากข้อมูล test นี้ แปลว่าใช้ test เลือกแล้ว ต้องรายงานตามนั้นและหาข้อมูลที่ยังไม่ใช้สำหรับประเมินใหม่ ตัวอย่างนี้จึงคงการเลือก Ridge จาก validation และรายงานผลที่เกิดจริง

</details>

<details><summary>6. Final R² เท่ากับ 0.88 พิสูจน์ว่าโมเดลทำกำไรได้หรือไม่</summary>

ไม่พิสูจน์ เราอธิบายผลตอบแทนกองทุนโดยใส่ผลตอบแทนปัจจัยเดือนเดียวกัน การสร้างกลยุทธ์ล่วงหน้าต้องจัด timing ของข้อมูล สัญญาณ น้ำหนักพอร์ต และค่าใช้จ่ายต่างหาก

</details>

<details><summary>7. Loading เปลี่ยนเมื่อเพิ่มข้อมูลจาก 60 เป็น 96 เดือน ต้องแปลว่าเกิด regime change หรือไม่</summary>

ไม่จำเป็น ตัวอย่างนี้ใช้ loading จริงคงที่ แต่ค่าประมาณยังเปลี่ยนจาก noise และปัจจัยที่สัมพันธ์กันสูง การอ้าง regime change ต้องมีหลักฐานและวิธีทดสอบเพิ่มเติม

</details>

<details><summary>8. RMSE = 0.012 ในหน่วยทศนิยมรายเดือน แสดงเป็นจุดเปอร์เซ็นต์เท่าไร</summary>

คูณ 100 ได้ 1.2 จุดเปอร์เซ็นต์ต่อเดือน อย่ารายงาน 0.012% และอย่าใช้ตัวเลขนี้เป็นผลตอบแทนคาดหวัง เพราะมันเป็นขนาด error

</details>

<span id="factor-validation-sources"></span>

## แหล่งอ่านและขอบเขตที่ปรับจาก Lab

อ่าน Transcript ฉบับเต็มของ [Penalty Methods](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/xvqVH/penalty-methods), [Setting Factor Loadings](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/0Qh5m/setting-factor-loadings-and-examples) และ [Factor Models Lab](https://www.coursera.org/learn/python-machine-learning-for-investment-management/lecture/zxZH1/lab-session-jupiter-notebook-on-factor-models) ตรวจเมื่อ 3 ตุลาคม 2026 Lab แยกข้อมูลก่อนปี 2013 ออกจากสองปีสุดท้าย และสาธิต K-fold สำหรับเลือก penalty ขณะที่ตัวอย่างที่เขียนใหม่หน้านี้ใช้ expanding-window ภายใน development โดยเฉพาะ

รายละเอียดการเดินเวลาอ้างอิง [TimeSeriesSplit](https://scikit-learn.org/1.6/modules/generated/sklearn.model_selection.TimeSeriesSplit.html), การตั้งคะแนนและ refit ดู [GridSearchCV](https://scikit-learn.org/1.6/modules/generated/sklearn.model_selection.GridSearchCV.html) และการป้องกันข้อมูลรั่วขณะปรับสเกลดู [Common Pitfalls](https://scikit-learn.org/1.6/common_pitfalls.html) ใช้ [StandardScaler](https://scikit-learn.org/1.6/modules/generated/sklearn.preprocessing.StandardScaler.html) ภายใน Pipeline แทนการละขั้นตอนปรับสเกลเพื่อความสั้นของตัวอย่าง

ทุกคะแนนมาจากข้อมูลสมมติและ seed ที่แสดงไว้ ไม่มีการแจกข้อมูลหรือโค้ดของคอร์ส และไม่มีการใช้คะแนนชุดทดสอบเปลี่ยนลำดับผู้ชนะหลังเลือกเสร็จ
