# Takenote — NoSQL (Phạm Gia Khánh)

> Mục đích: bộ nhớ ngắn gọn, dùng lại khi làm đồ án. Nguồn đã đọc: `Chương 1. Giới thiệu NoSQL.md`, `Chương 2. MongoDB.md`, `TH_HUONG DAN THUC HANH NoSQL_2025.md`, `zips.json`, `restaurants.json`.
>
> Quy ước: **[Tài liệu]** là nội dung giảng dạy; **[Thực hành tốt]** là bổ sung kỹ thuật cần dùng khi triển khai hiện đại. Không coi slide cũ là API hiện hành nếu có mâu thuẫn.

## 1. Phạm vi môn học

- Bốn nhóm NoSQL: Key–Value, Column-family, Graph, Document.
- Hệ quản trị có thực hành: **MongoDB**, **Cassandra**, **Neo4j**. Redis chỉ có lý thuyết tổng quan; phần thực hành Redis bị thiếu.
- Tiêu chí ngầm cho đồ án: mô hình dữ liệu hợp use case, dữ liệu mẫu, CRUD, truy vấn nâng cao/thống kê, index hoặc chứng minh hiệu năng, ứng dụng kết nối CSDL. Không thấy rubric chính thức.

## 2. Lý thuyết lõi

- NoSQL: phi quan hệ; ưu tiên linh hoạt schema, throughput, phân tán, mở rộng ngang.
- SQL hợp dữ liệu/ràng buộc ổn định, cần nhất quán mạnh. NoSQL hợp dữ liệu thay đổi, quy mô/traffic lớn, quan hệ không cần join kiểu RDBMS.
- Eventual consistency: bản sao có thể lệch tạm thời sau ghi nhưng sẽ hội tụ.
- High availability: replication để node hỏng không làm toàn hệ thống dừng.
- Vertical scaling = tăng tài nguyên một máy; horizontal scaling = thêm node.
- CAP, BASE vs ACID, sharding/replica topology, Cassandra consistency levels: chỉ được nhắc hoặc chưa giải thích đủ; cần giải thích riêng nếu đồ án dùng các chủ đề này.

## 3. Chọn loại CSDL

| Loại | Mô hình / dùng khi nào | Hệ QTCSDL |
|---|---|---|
| Key–Value | `key -> value`; cache, session, profile, pub/sub | Redis |
| Column-family | query-first, ghi/phân tán lớn, không join | Cassandra |
| Graph | node + relationship + property; quan hệ nhiều tầng, gợi ý, social | Neo4j |
| Document | collection chứa BSON/JSON; dữ liệu lồng nhau, linh hoạt | MongoDB |

## 4. MongoDB — kiến thức dùng trực tiếp

### Mô hình dữ liệu

- Cấu trúc: database -> collection -> document -> field. Mỗi document có `_id` duy nhất.
- BSON có String, Number, Boolean, Date, ObjectId, array, embedded object, binary, regex…
- **Embedded**: dữ liệu con thường đọc/cập nhật cùng cha, số lượng bị chặn hợp lý. Ví dụ: `order.items`, `post.comments`.
- **Reference**: dữ liệu dùng chung, many-to-many, hoặc mảng con có thể tăng vô hạn. Lưu ID và truy vấn riêng/`$lookup` khi thật cần.
- Tài liệu dùng `sv` (Lop embedded, Ngoaingu array, Monhoc array) và `hoadon` (Khachhang embedded, SanphamBan array).

### CRUD hiện hành ưu tiên

```javascript
db.coll.insertOne(doc); db.coll.insertMany([doc1, doc2])
db.coll.find(filter, projection); db.coll.findOne(filter)
db.coll.updateOne(filter, {$set: {...}}); db.coll.updateMany(filter, {$set: {...}})
db.coll.deleteOne(filter); db.coll.deleteMany(filter)
```

- Field nhúng: `{"Lop.Malop": "l01"}`.
- Vị trí mảng: `{"Ngoaingu.1": "Tiếng Nhật"}`; phần tử document mảng: `{"Monhoc.0.Diem": 9}`.
- Mảng: `$push` (có thể trùng), `$addToSet` (không trùng), `$pull` (xóa phần tử).
- Truy vấn: equality, `$in`, regex (`/^Trần/`), `$eq/$ne/$lt/$lte/$gt/$gte`, `$and/$or`, `$elemMatch`, projection, `sort`, `skip`, `limit`.

### Aggregation / index

- Pipeline thường dùng: `$match`, `$project`, `$unwind`, `$group`, `$sort`, `$skip`, `$limit`.
- Accumulator: `$sum`, `$avg`, `$min`, `$max`, `$push`, `$addToSet`, `$first`, `$last`; `$size` dùng trong `$project`.
- Index: `_id` mặc định; đơn, compound, sparse, unique. Đọc nhanh hơn nhưng ghi tốn hơn.
- Chỉ index theo filter/sort thực tế; dùng `explain("executionStats")` để chứng minh. Ví dụ dataset zip: `db.zips.createIndex({state:1, city:1, pop:1})`.

### Các API cũ trong tài liệu

- Không dùng làm code mới: `mongo`, `insert`, `update`, `remove`, `save`, C# `GetServer`, `FindAll`, `Insert`, `Remove`.
- Dùng `mongosh`, phương thức `*One/*Many`, driver MongoDB hiện hành. Tài liệu dùng API cũ vì dựa trên MongoDB/driver cũ.

## 5. Cassandra — kiến thức dùng trực tiếp

- `Keyspace` tương tự database; table/column family bên trong. Không foreign key, không join khi truy vấn.
- Thiết kế **theo truy vấn**; có thể tạo nhiều table chứa dữ liệu lặp để phục vụ các câu truy vấn khác nhau.
- `PRIMARY KEY ((partition_key...), clustering_key...)`:
  - partition key định vị partition và phải có trong truy vấn thông thường;
  - clustering key sắp xếp các row trong partition và dùng `ORDER BY`.
- Ví dụ: `hotels_by_poi(poi_name, hotel_id, ...)`, `PRIMARY KEY (poi_name, hotel_id)`; tìm khách sạn theo địa điểm tham quan.
- CQL: `CREATE/ALTER/DROP KEYSPACE`, `CREATE/ALTER/DROP TABLE`, `INSERT`, `UPDATE`, `DELETE`, `SELECT`.
- Hạn chế `ALLOW FILTERING`: thường là dấu hiệu cần tạo table truy vấn riêng.
- C# trong tài liệu: CassandraCSharpDriver + prepared statements (`Prepare`, `Bind`, `Execute`).

## 6. Neo4j — kiến thức dùng trực tiếp

- Node có label/properties; relationship có type, hướng/properties.
- Mẫu: `(p:Person)-[:LIKES]->(t:Technology)`.
- CRUD Cypher: `CREATE`, `MATCH`, `SET`, `REMOVE`, `DELETE`, `DETACH DELETE`.
- Truy vấn: `WHERE`, `IN`, `STARTS WITH`, `CONTAINS`, regex, pattern existence, `WITH`, `UNWIND`, `DISTINCT`, `ORDER BY`, `LIMIT`.
- Tổng hợp: `count`, `avg`, `sum`, `min`, `max`, `collect`, `size`.
- Nên tạo unique constraint/index cho ID nghiệp vụ và dùng `MERGE` khi cần tránh node/relationship trùng.
- Java trong tài liệu dùng Neo4j Java Driver/Bolt; truyền tham số qua `Map<String,Object>`, không nối chuỗi input vào Cypher.

## 7. Dataset có sẵn

- `zips.json`: 29,353 JSON Lines; `_id`, `city`, `state`, `pop`, `loc`; 51 bang, 16,584 thành phố. Dùng cho index/explain.
- `restaurants.json`: 10,000 JSON array; `_id`, `name`, `contact{phone,email,location}`, `grades[]`, `stars`, `categories[]`. Dùng cho nested query, array và aggregation.

## 8. Hướng đồ án phù hợp

1. **MongoDB — bán hàng/đặt đồ ăn**: orders nhúng line-items + customer snapshot; dashboard aggregation, index, CRUD app. Phù hợp nhất nếu cần làm nhanh/bám tài liệu.
2. **Neo4j — gợi ý sản phẩm/chăm sóc khách hàng**: Customer–Product–Purchase–Interest–Staff; mạnh ở quan hệ/gợi ý.
3. **Cassandra — đặt vé/tour/học trực tuyến**: tạo bảng theo từng màn hình truy vấn; thể hiện tư duy query-first.

## 9. Điểm cần kiểm chứng trước khi dùng

- Lệnh slide `db.cropDatabase()` sai; đúng là `db.dropDatabase()`.
- Một ví dụ Mongo aggregation yêu cầu lọc nhân viên nam nhưng thiếu `$match` theo `Phai`.
- Một ví dụ mô tả số môn không thống nhất điều kiện `>= 3`/"từ 2".
- Cassandra slide diễn giải `ORDER BY` trên partition key là không chuẩn; chỉ dùng clustering column sau khi xác định partition.
- Neo4j slide có lỗi biến `MATCH (p...) DETACH DELETE n` và điều kiện chuỗi `20<=p.age<=30`; phải dùng biến đúng và `p.age >= 20 AND p.age <= 30`.
- Chương Redis thực hành không có nội dung dù mục lục ghi có.

## 10. Cassandra — bổ sung từ Chương 3

### Kiến trúc và độ bền dữ liệu

- Cassandra là CSDL phân tán, peer-to-peer; node trao đổi trạng thái qua gossip và có replication giữa node/datacenter.
- Đường ghi: ghi vào **commit log** trên đĩa và **memtable** trong bộ nhớ; khi memtable đầy/được flush, dữ liệu thành **SSTable** bất biến trên đĩa. Commit log giúp khôi phục ghi chưa flush khi node lỗi.
- SSTable không sửa tại chỗ; update/delete tạo phiên bản/tombstone mới. Compaction hợp nhất SSTable để giảm chồng lấp và thu hồi dữ liệu đã hết hiệu lực.
- Compaction: **STCS** gom SSTable có kích thước tương tự; **LCS** chia SSTable theo level, hạn chế chồng lấp trong từng level. Đây là kiến thức kiến trúc, chưa cần tự cấu hình trong đồ án cơ bản.

### Thiết kế query-first

- Mỗi table phục vụ một truy vấn chính; một query mới quan trọng có thể cần table/materialized view mới. Không thiết kế theo chuẩn hóa và join như RDBMS.
- `PRIMARY KEY ((a,b), c, d)`: `(a,b)` là composite partition key; `c,d` là clustering columns. Partition key quyết định nơi dữ liệu nằm; clustering columns quyết định thứ tự trong partition và có thể khai báo `ASC/DESC`.
- Ví dụ khách sạn: `hotels_by_poi(poi_name, hotel_id, ...)` phục vụ tìm khách sạn gần điểm tham quan; `hotels(hotel_id, ...)` phục vụ xem chi tiết theo mã khách sạn. Dữ liệu lặp là chủ ý để tối ưu query.
- Tránh partition quá lớn/nóng; chọn partition key sao cho phân bố đều và giới hạn số row theo một key.

### CQL và kiểu dữ liệu nâng cao

- Keyspace: `CREATE/ALTER/DROP KEYSPACE`; replication dùng `SimpleStrategy` cho môi trường đơn giản/một DC, `NetworkTopologyStrategy` khi có nhiều datacenter. `durable_writes=false` giảm độ bền, không dùng mặc định cho dữ liệu nghiệp vụ.
- Table: `CREATE/ALTER/DROP TABLE`; CRUD: `INSERT`, `UPDATE`, `DELETE`, `SELECT`. `INSERT` trong Cassandra có tính upsert: cùng primary key sẽ ghi/cập nhật row.
- Collection: `list`, `set`, `map`; chỉ dùng cho tập dữ liệu nhỏ và bị chặn. `map` hợp lưu cặp key–value; `set` loại trùng; `list` giữ thứ tự nhưng không phù hợp làm lịch sử tăng vô hạn.
- UDT (user-defined type) mô tả object có cấu trúc; có thể dùng `frozen<udt>` trong collection khi cần lưu value như một đơn vị.
- Materialized view tạo cách truy cập khác từ base table khi các cột khóa không null. Với đồ án, ưu tiên table riêng cho query quan trọng; chỉ dùng MV khi hiểu chi phí ghi/nhất quán và có lý do rõ.

### Thao tác và kết nối

- Công cụ được nêu: TablePlus; bài cũ còn nhắc JDK 8, Python 2.7, Cassandra 3.11.4 cho Windows — chỉ là môi trường lịch sử, cần kiểm tra tương thích nếu cài bản mới.
- Kiểm tra node: `nodetool status`. Cấu hình nằm trong `conf/`; hạn chế swap và dùng power profile hiệu năng cao theo khuyến nghị tài liệu.
- C# driver: dùng `Cluster.Builder().AddContactPoint(...).Build()`, `session.Prepare(...)`, `Bind(...)`, `Execute(...)`; prepared statement là cách chuẩn cho query có tham số.

### Cảnh báo từ tài liệu nguồn

- File Markdown bị lỗi OCR/chuyển đổi ở nhiều câu lệnh (tên `hotels_by_poi` bị tách, dấu nháy và JSON sai, `DROP TABLE hotels description` sai cú pháp). Không chạy nguyên văn các đoạn đó; kiểm tra CQL chuẩn trước khi dùng.
- Tài liệu cài đặt dựa trên Cassandra 3.11.4/Python 2.7 và nội dung trang web năm 2019–2020, nên không dùng làm hướng dẫn phiên bản hiện hành.
