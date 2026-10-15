# Quay Đội

Bốc thăm đội, ghi tỉ số và tạo poster cho những trận đá game (eFootball/FC) cùng bạn bè.
App web cài được (PWA), chạy offline, dữ liệu chỉ nằm trên điện thoại người dùng.

## Dùng
Mở link GitHub Pages của repo này trên điện thoại:
- Android: Chrome → ⋮ → **Cài đặt ứng dụng**
- iPhone: Safari → Chia sẻ → **Thêm vào MH chính**

## Tính năng (v1.0.1)
- Mỗi người tự bấm quay 1 lần; chế độ Cân bằng / Lệch nhẹ / Chấp / Ngẫu nhiên; không lặp đội gần đây
- Hủy trận, đá lại do lỗi, tái đấu, sửa tỉ số
- Buổi đá, thống kê đối đầu theo từng người chơi, phong độ
- Poster trận đấu và poster tổng kết buổi (chia sẻ ảnh)
- Tên đội trong game, bật/tắt đội, hạng sao
- Sao lưu / khôi phục (file hoặc mã), làm mới thống kê, reset

## Cấu trúc
- `index.html`, `sw.js`, `manifest.webmanifest`, icon: bản chạy (GitHub Pages phục vụ trực tiếp)
- `dev/index.src.html` + `dev/build.py`: mã nguồn và script đóng gói (nhúng font Be Vietnam Pro)
- `dev/test/`: kiểm thử tự động bấm mọi nút (Playwright)

Font Be Vietnam Pro — SIL Open Font License 1.1.
