# Tai lieu giai thich cac phan analysis

Dashboard nay phan tich review cua hanh khach ve BTS Skytrain theo sentiment tong quan va aspect-based sentiment analysis (ABSA). Muc tieu la bien review thanh bang chung de uu tien cai thien dich vu.

Neu can huong dan cach doc tung bang, KPI card va bieu do, xem them `docs/dashboard_observation_guide.md`.

## 1. Data scope va filters

Phan filter o sidebar quyet dinh toan bo du lieu duoc tinh trong dashboard.

- `BTS-service relevant only`: chi giu cac review co lien quan truc tiep den dich vu BTS.
- `Source`: loc theo nguon review, vi du Tripadvisor, Reddit, Klook.
- `BTS line`: loc theo tuyen hoac khu vuc BTS duoc gan trong dataset.
- `Overall sentiment`: loc theo nhan Negative, Neutral, Positive trong cot `Final_Label`.
- `Service aspect`: loc cac review lien quan den mot hoac nhieu khia canh dich vu.
- `Rating range`: loc theo `review_rating_num`, day la diem 1-5 suy ra tu sentiment.
- `Minimum agreement count`: loc cac review co muc do dong tinh/tuong tac toi thieu.
- `Analysis date range`: loc theo ngay review de bieu do sentiment theo thoi gian, KPI, aspect analysis va bang review cung dung cung mot khoang thoi gian.
- `Sentiment time aggregation`: gom bieu do sentiment theo thang, quy hoac nam.

## 2. Executive Overview

Day la man hinh tong quan cho cau hoi: tinh hinh dich vu hien tai dang tot hay xau, va van de nao can uu tien.

### KPI cards

- `Total reviews`: tong so dong trong CSV goc.
- `Filtered reviews`: so review con lai sau tat ca filter hien tai.
- `Average rating`: diem trung binh tu `review_rating_num`.
- `Negative share`: ty le review co `Final_Label = Negative`.
- `Agreement count`: tong `like_count` da duoc doi ten thanh `agreement_count`.

### Sentiment over time

Bieu do nay cho thay sentiment tang/giam theo khoang thoi gian da chon. Khi chon `Review count`, truc Y la so review. Khi chon `Sentiment share`, truc Y la ty le cua tung sentiment trong tung ky.

Truc X hien ro nhan thoi gian:

- Monthly: `YYYY-MM`
- Quarterly: `YYYY Qn`
- Yearly: `YYYY`

Dung bieu do nay de xem review tieu cuc tang vao thang/quy/nam nao, hoac sentiment tich cuc co giam sau mot giai doan nao khong.

### Overall sentiment

Bieu do nay tom tat tong so review Negative, Neutral va Positive trong pham vi filter hien tai. No tra loi cau hoi: sentiment chung cua hanh khach dang nghieng ve huong nao.

### Top service pain points

Bieu do nay xep hang cac aspect dich vu theo `Priority score`. Aspect co diem cao la noi co nhieu review tieu cuc va/hoac review tieu cuc co nhieu agreement.

### Model checkpoint

Bang nay so sanh nhan cua Logistic Regression va DistilBERT. Ty le agreement cao cho thay hai model kha nhat quan, con cac cap nhan khac nhau la diem can xem lai neu muon cai thien model.

## 3. Aspect Priority Dashboard

Man hinh nay dung de phan tich chi tiet tung khia canh dich vu.

### ABSA sentiment heatmap

Heatmap hien so review Negative, Neutral, Positive cho tung aspect. O nao dam hon nghia la co nhieu review hon. Dung de nhin nhanh aspect nao bi phan nan nhieu nhat.

### Priority ranking

Bang ranking hien:

- `Mentions`: so review co lien quan den aspect.
- `Negative`: so review tieu cuc cua aspect.
- `Neutral`: so review trung lap cua aspect.
- `Positive`: so review tich cuc cua aspect.
- `Negative agreement`: tong agreement cua cac review tieu cuc.
- `Priority score`: cong thuc uu tien xu ly.
- `Negative share`: ty le tieu cuc trong cac mention cua aspect.

Cong thuc:

```text
Priority score = Negative review count + 0.1 x Negative agreement count
```

### Aspect drilldown

Dropdown nay cho phep chon mot aspect cu the. Sau khi chon, dashboard hien KPI rieng cua aspect do va cac review bang chung co agreement cao.

### Highest-agreement evidence

Bang nay hien cac review tieu cuc co agreement cao nhat cho aspect dang chon. Day la bang chung tot de dua vao phan business recommendation.

### Aspect sentiment over time

Bieu do nay chi tinh sentiment cua aspect dang chon theo thoi gian. No giup tra loi: van de cua aspect nay dang tang hay giam trong khoang ngay da loc.

## 4. Rating vs Agreement

Man hinh nay tach biet diem sentiment voi muc do dong tinh/tuong tac.

### Rating and agreement scatter

Moi diem la mot review:

- Truc X: `review_rating_num`, diem 1-5 suy ra tu sentiment.
- Truc Y: `agreement_count`, so upvote/helpful vote/tuong tac.
- Mau: sentiment Negative, Neutral, Positive.

Mot review co agreement cao khong co nghia la review tich cuc. Neu review do negative va co nhieu agreement, no la complaint quan trong.

### Sentiment trend in the selected period

Bieu do nay lap lai xu huong sentiment trong khoang filter hien tai, giup doi chieu voi scatter va complaint table.

### High-agreement, low-rating complaints

Bang nay loc cac complaint co:

- `Final_Label = Negative`
- rating thap
- agreement cao hon threshold nguoi dung chon

Day la danh sach uu tien de trich dan lam evidence.

## 5. Operational Actions

Man hinh nay bien analysis thanh goi y hanh dong cho cac aspect chinh:

- Crowding & Comfort
- Fare & Payment System
- Infrastructure & Facilities
- Route Coverage & Connectivity

Moi tab gom:

- muc tieu cai thien,
- KPI cua aspect,
- recommended business actions,
- success metrics can theo doi,
- review evidence de ho tro quyet dinh.

## 6. Review Explorer

Day la noi tim review goc theo tu khoa va xem evidence card.

- `Search review text`: tim trong noi dung review.
- `Rows to show`: chon so dong hien thi.
- Bang review hien title, snippet, source, rating, agreement, primary aspect, sentiment va link review.
- Evidence card hien thong tin tom tat cua mot review duoc chon.

## 7. Data rules quan trong

`review_rating_num` la diem 1-5 suy ra tu sentiment, khong dung upvote lam rating.

`like_count` duoc doi thanh `agreement_count`. Gia tri nay do muc do dong tinh hoac tuong tac voi review. Vi vay, mot review negative co upvote cao van la review negative, nhung la complaint co trong so cao hon.

`Final_Label` la nhan sentiment tong quan cuoi cung.

Cot `sentiment_*` la sentiment theo tung aspect trong ABSA.

`primary_aspect` la aspect chinh cua review.
