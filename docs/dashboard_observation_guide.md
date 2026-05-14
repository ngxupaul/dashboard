# Huong dan quan sat tung bang va bieu do

Tai lieu nay giai thich cach doc tung bang, KPI card va bieu do trong dashboard. Khi quan sat, luon doc theo thu tu: filter dang ap dung, khoang ngay, sentiment, aspect, bang evidence.

## 1. Sidebar filters

Muc dich: gioi han pham vi phan tich truoc khi doc cac bang va bieu do.

Cach quan sat:

- Xem `BTS-service relevant only` co bat khong. Neu bat, dashboard chi tinh review lien quan den dich vu BTS.
- Xem `Analysis date range` de biet tat ca KPI, trend, aspect va review table dang nam trong khoang ngay nao.
- Xem `Sentiment time aggregation` de biet line chart dang gom theo thang, quy hay nam.
- Neu filter source, line, sentiment hoac aspect qua hep, so `Filtered reviews` se giam va cac bieu do co the bien dong manh hon.

Ket luan can rut:

- Truoc khi noi ve insight, phai noi ro dang phan tich pham vi nao.
- Neu doi filter, tat ca bang va bieu do ben duoi deu thay doi theo.

## 2. Executive Overview - KPI cards

Bang/KPI:

- `Total reviews`
- `Filtered reviews`
- `Average rating`
- `Negative share`
- `Agreement count`

Cach quan sat:

- So sanh `Filtered reviews` voi `Total reviews` de biet filter dang loai bao nhieu dong.
- `Average rating` cao nhung `Negative share` van dang ke thi van can doc aspect, vi mot so van de co the tap trung o mot khia canh cu the.
- `Agreement count` cao cho thay co nhieu tuong tac/upvote/helpful vote trong pham vi filter.

Ket luan can rut:

- KPI cards tra loi nhanh: quy mo du lieu la bao nhieu, sentiment chung ra sao, va muc do tuong tac cua review co lon khong.

## 3. Executive Overview - Sentiment over time

Loai bieu do: line chart.

Cach quan sat:

- Truc X la thoi gian: monthly hien `YYYY-MM`, quarterly hien `YYYY Qn`, yearly hien `YYYY`.
- Truc Y la `Review count` hoac `Sentiment share` tuy radio dang chon.
- Duong mau do la Negative, xam la Neutral, xanh la Positive.
- Tim cac diem Negative tang dot bien, Positive giam dot bien, hoac Neutral tang cao.
- Doi sang `Sentiment share` neu muon so sanh ty le sentiment giua cac ky co so luong review khac nhau.

Ket luan can rut:

- Neu Negative tang trong mot thang/quy cu the, can qua bang evidence de doc review cung giai doan.
- Neu Positive chiem ty le cao nhung Negative van tang, day la dau hieu van de cu the dang noi len trong mot nhom review.

## 4. Executive Overview - Overall sentiment

Loai bieu do: bar chart.

Cach quan sat:

- So sanh chieu cao ba cot Negative, Neutral, Positive.
- Neu Positive cao hon nhieu, sentiment tong quan tot.
- Neu Negative chiem ty le dang ke, can doc tiep `Top service pain points` de biet nguyen nhan.

Ket luan can rut:

- Bieu do nay cho anh nhin tong quan, khong du de ket luan can sua dich vu nao.
- Luon ket hop voi aspect ranking va evidence table.

## 5. Executive Overview - Top service pain points

Loai bieu do: horizontal bar chart.

Cach quan sat:

- Doc tu tren xuong theo `Priority score`.
- Aspect dung dau la diem dau dich vu can uu tien.
- Diem cao co the den tu nhieu review Negative, hoac it review Negative nhung co agreement cao.

Ket luan can rut:

- Dung bieu do nay de chon 3-4 aspect quan trong nhat cho phan business recommendation.
- Sau khi chon aspect, qua `Aspect Priority Dashboard` de xem chi tiet va evidence.

## 6. Executive Overview - Model checkpoint

Bang/KPI:

- KPI `LR vs DistilBERT agreement`
- Bang cap nhan `LogisticRegression_Label`, `DistilBERT_Label`, `Reviews`

Cach quan sat:

- KPI agreement cao nghia la hai model nhat quan tren phan lon review.
- Trong bang, dong co cung nhan o hai cot la truong hop hai model dong y.
- Dong co hai nhan khac nhau la truong hop can xem lai neu muon danh gia chat luong model.
- `Reviews` cang cao thi cap nhan do cang pho bien.

Ket luan can rut:

- Bang nay khong phai insight kinh doanh truc tiep. No la checkpoint de chung minh pipeline sentiment co tinh on dinh tuong doi.

## 7. Aspect Priority Dashboard - ABSA sentiment heatmap

Loai bieu do: heatmap.

Cach quan sat:

- Hang la aspect dich vu.
- Cot la sentiment Negative, Neutral, Positive.
- So trong o la so review.
- Mau dam hon nghia la so review nhieu hon.
- Tap trung vao o Negative dam va co gia tri cao.

Ket luan can rut:

- Heatmap giup nhin nhanh aspect nao co nhieu review tieu cuc.
- Neu mot aspect vua co Positive cao vua co Negative cao, dich vu do co trai nghiem phan hoa, can doc review evidence de hieu nguyen nhan.

## 8. Aspect Priority Dashboard - Priority ranking

Loai bang: ranking table.

Cot can doc:

- `Aspect`: khia canh dich vu.
- `Mentions`: so review nhac den aspect.
- `Negative`: so review tieu cuc cua aspect.
- `Neutral`: so review trung lap cua aspect.
- `Positive`: so review tich cuc cua aspect.
- `Negative agreement`: tong agreement cua review tieu cuc.
- `Priority score`: diem uu tien xu ly.
- `Negative share`: ty le tieu cuc trong review nhac den aspect.

Cach quan sat:

- Sap xep mac dinh theo `Priority score`, doc tu tren xuong.
- So sanh `Negative` voi `Mentions` de biet van de co pho bien khong.
- So sanh `Negative agreement` de biet complaint co duoc nhieu nguoi dong tinh khong.
- `Negative share` cao nhung `Mentions` thap co the la van de nho nhung nghiem trong trong nhom review lien quan.

Ket luan can rut:

- Chon aspect uu tien dua tren ca `Priority score`, `Negative`, `Negative agreement` va `Negative share`, khong chi nhin mot cot.

## 9. Aspect Priority Dashboard - Aspect drilldown KPI

Bang/KPI:

- `Mentions`
- `Negative`
- `Negative agreement`
- `Priority score`

Cach quan sat:

- Sau khi chon aspect, doc 4 KPI nay de biet quy mo va muc do nghiem trong rieng cua aspect.
- `Negative agreement` cao la dau hieu review tieu cuc co nhieu nguoi dong tinh.
- `Priority score` cao la dau hieu aspect nay nen duoc dua vao action plan.

Ket luan can rut:

- KPI drilldown giup bien ranking tong quan thanh cau chuyen chi tiet cho mot aspect cu the.

## 10. Aspect Priority Dashboard - Highest-agreement evidence

Loai bang: evidence table.

Cot can doc:

- `Title`: tieu de review.
- `Review snippet`: doan noi dung tom tat.
- `Source`: nguon review.
- `Rating`: diem 1-5 suy ra tu sentiment.
- `Agreement count`: so tuong tac/upvote/helpful vote.
- `Primary aspect`: aspect chinh.
- `Sentiment`: sentiment tong quan.
- `Review link`: link review goc.

Cach quan sat:

- Doc tu tren xuong vi bang uu tien review co agreement cao.
- Uu tien review co `Sentiment = Negative`, `Rating` thap va `Agreement count` cao.
- Dung `Review snippet` de tim nguyen nhan cu the, vi du crowding, ticket, elevator, transfer, wayfinding.
- Mo `Review link` khi can trich dan bang chung goc.

Ket luan can rut:

- Bang nay la nguon evidence cho recommendation. Khong nen chi dua vao score ma bo qua noi dung review.

## 11. Aspect Priority Dashboard - Aspect sentiment over time

Loai bieu do: line chart theo aspect.

Cach quan sat:

- Chon mot aspect trong `Aspect drilldown`.
- Doc Negative/Neutral/Positive cua rieng aspect do theo thoi gian.
- Neu Negative cua aspect tang trong mot ky, kiem tra evidence cua aspect do.
- Doi giua `Review count` va `Sentiment share` de phan biet tang do nhieu review hon hay tang ve ty le.

Ket luan can rut:

- Bieu do nay giup noi duoc van de cua aspect dang tot len, xau di, hay chi xuat hien trong mot giai doan.

## 12. Rating vs Agreement - Scatter chart

Loai bieu do: scatter plot.

Cach quan sat:

- Moi diem la mot review.
- Truc X la `review_rating_num`.
- Truc Y la `agreement_count`.
- Diem nam ben trai va cao la review rating thap nhung agreement cao.
- Mau diem cho biet sentiment.

Ket luan can rut:

- Review negative co agreement cao la complaint co trong so lon.
- Upvote/agreement khong duoc xem la rating. No chi cho biet muc do dong tinh hoac tuong tac.

## 13. Rating vs Agreement - Sentiment trend in selected period

Loai bieu do: line chart.

Cach quan sat:

- Doc giong `Sentiment over time`, nhung trong context cua trang rating vs agreement.
- Dung de xem giai doan dang co complaint rating thap co trung voi dot Negative tang khong.

Ket luan can rut:

- Neu scatter co nhieu complaint cao agreement va trend cung co Negative tang, insight se manh hon.

## 14. Rating vs Agreement - High-agreement, low-rating complaints

Loai bang: complaint table.

Cot can doc:

- `Title`
- `Review snippet`
- `Source`
- `Rating`
- `Agreement count`
- `Primary aspect`
- `Sentiment`
- `Review link`

Cach quan sat:

- Dieu chinh threshold `High-agreement complaint threshold`.
- Threshold thap cho nhieu complaint hon, threshold cao chi giu complaint duoc nhieu nguoi dong tinh.
- Uu tien dong co `Rating` 1-2 va `Agreement count` cao.
- Doc `Primary aspect` de gom complaint thanh nhom van de.

Ket luan can rut:

- Bang nay dung de tim complaint co gia tri thuyet phuc cao khi viet recommendation.

## 15. Operational Actions - KPI trong tung tab

Loai KPI/action panel.

Cach quan sat:

- Moi tab la mot aspect hanh dong chinh.
- Doc `Negative reviews`, `Positive reviews`, `Agreement weight`, `Priority score`.
- So sanh Negative va Positive de biet aspect do bi phan nan nhieu hay van co trai nghiem tot song song.
- `Agreement weight` cao cho thay complaint co suc nang trong cong dong review.

Ket luan can rut:

- KPI trong tab giup bien aspect priority thanh uu tien hanh dong cu the.

## 16. Operational Actions - Recommended business actions

Loai danh sach hanh dong.

Cach quan sat:

- Moi bullet la mot hanh dong de giai quyet aspect dang chon.
- Doi chieu hanh dong voi KPI va evidence review ben phai.
- Neu action khong duoc evidence ho tro, khong nen dua vao ket luan chinh.

Ket luan can rut:

- Phan nay dung de viet business recommendation, khong phai de do luong model.

## 17. Operational Actions - Success metrics to track

Loai danh sach metric.

Cach quan sat:

- Moi metric la chi so nen theo doi sau khi thuc hien action.
- Chon metric gan voi van de trong evidence, vi du crowding, fare/payment, facility, route/connectivity.

Ket luan can rut:

- Recommendation tot can co metric theo doi, khong chi neu hanh dong.

## 18. Operational Actions - Evidence reviews

Loai bang: evidence table theo aspect.

Cach quan sat:

- Doc review co agreement cao truoc.
- Kiem tra source, rating, primary aspect va snippet.
- Dung bang nay de chung minh tai sao action duoc de xuat.

Ket luan can rut:

- Evidence reviews la cau noi giua phan analysis va phan operational action.

## 19. Review Explorer - Review table

Loai bang: searchable review table.

Cot can doc:

- `Title`
- `Review snippet`
- `Source`
- `Rating`
- `Agreement count`
- `Primary aspect`
- `Sentiment`
- `Review link`

Cach quan sat:

- Nhap keyword vao `Search review text`, vi du `Rabbit Card`, `crowded`, `elevator`, `Asok`, `ticket`.
- Tang/giam `Rows to show` de xem nhieu hoac it review.
- Sap xep logic hien tai uu tien agreement cao va rating thap.
- Dung bang nay de tim example cho mot van de rat cu the.

Ket luan can rut:

- Review Explorer dung cho dieu tra sau khi da thay pattern tren chart hoac ranking.

## 20. Review Explorer - Evidence card

Loai card chi tiet review.

Cach quan sat:

- Chon mot review trong dropdown `Evidence card`.
- Doc source, sentiment, rating, agreement va primary aspect.
- Doc snippet de xem review co phu hop lam bang chung khong.
- Mo link review goc neu can kiem tra ngu canh.

Ket luan can rut:

- Evidence card dung de chon review tieu bieu cho bao cao hoac thuyet trinh.

## 21. Cach doc dashboard theo mot workflow

Workflow de quan sat dung:

1. Chon filter va khoang ngay.
2. Doc KPI cards de biet quy mo va sentiment chung.
3. Doc `Sentiment over time` de tim giai doan sentiment tang/giam.
4. Doc `Top service pain points` de chon aspect uu tien.
5. Qua `Aspect Priority Dashboard` de xem heatmap, ranking va evidence.
6. Qua `Rating vs Agreement` de tim complaint rating thap nhung agreement cao.
7. Qua `Operational Actions` de chon action va success metrics.
8. Dung `Review Explorer` de tim review goc va trich dan.

## 22. Loi can tranh khi quan sat

- Khong ket luan chi dua vao `Average rating`.
- Khong xem `agreement_count` la rating.
- Khong ket luan aspect uu tien chi dua vao `Negative` ma bo qua `Negative agreement` va `Negative share`.
- Khong doc trend khi chua kiem tra `Analysis date range`.
- Khong dung review snippet lam bang chung cuoi cung neu chua mo link goc trong truong hop can trich dan chinh xac.
