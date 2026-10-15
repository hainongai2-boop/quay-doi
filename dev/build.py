"""Đóng gói Quay Đội thành PWA: nhúng font, sinh manifest, service worker, icon, hướng dẫn, zip."""
import base64, json, os, shutil, sys, zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'src', 'index.html')
DIST = os.path.join(ROOT, 'dist', 'quay-doi')
FONT_DIR = sys.argv[1]  # thư mục files/ của @fontsource/be-vietnam-pro
VERSION = '1.0.1'

RANGES = {
    'latin': 'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD',
    'latin-ext': 'U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF',
    'vietnamese': 'U+0102-0103,U+0110-0111,U+0128-0129,U+0168-0169,U+01A0-01A1,U+01AF-01B0,U+0300-0301,U+0303-0304,U+0308-0309,U+0323,U+0329,U+1EA0-1EF9,U+20AB',
}

def font_css():
    out = []
    for w in (700, 900):
        for sub in ('vietnamese', 'latin-ext', 'latin'):
            p = os.path.join(FONT_DIR, f'be-vietnam-pro-{sub}-{w}-normal.woff2')
            b64 = base64.b64encode(open(p, 'rb').read()).decode()
            out.append("@font-face{font-family:'BVP';font-style:normal;font-weight:%d;font-display:swap;"
                       "src:url(data:font/woff2;base64,%s) format('woff2');unicode-range:%s}" % (w, b64, RANGES[sub]))
    return '\n'.join(out)

MANIFEST = {
    "name": "Quay Đội — bốc thăm đội & tỉ số",
    "short_name": "Quay Đội",
    "description": "Bốc thăm đội, ghi tỉ số và tạo poster cho những trận đá game cùng bạn bè. Chạy offline.",
    "lang": "vi",
    "id": "./",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": "#0a120e",
    "theme_color": "#0a120e",
    "icons": [
        {"src": "icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
        {"src": "icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}
    ]
}

SW = """/* Quay Đội — service worker: chạy offline, tự cập nhật ở lần mở sau */
const CACHE = 'quaydoi-%s';
const ASSETS = ['./', './index.html', './manifest.webmanifest', './icon-192.png', './icon-512.png', './icon-maskable-512.png', './apple-touch-icon.png'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
function refresh(req, key) {
  return fetch(req).then(res => {
    if (res && res.ok) { const cp = res.clone(); caches.open(CACHE).then(c => c.put(key || req, cp)); }
    return res;
  });
}
self.addEventListener('fetch', e => {
  const r = e.request;
  if (r.method !== 'GET' || new URL(r.url).origin !== location.origin) return;
  if (r.mode === 'navigate') {
    e.respondWith(caches.match('./index.html').then(c => {
      const net = refresh(r, './index.html').catch(() => c);
      return c || net;
    }));
    return;
  }
  e.respondWith(caches.match(r).then(c => {
    const net = refresh(r).catch(() => c);
    return c || net;
  }));
});
""" % VERSION

GUIDE = """QUAY ĐỘI v%s — HƯỚNG DẪN CÀI VÀO ĐIỆN THOẠI
==================================================

Thư mục này là một app web cài được (PWA). Để cài ra màn hình chính
và chạy offline, app cần được mở từ một link https một lần.
Làm 1 lần duy nhất, mất khoảng 5 phút, miễn phí.

--------------------------------------------------
BƯỚC 1 — ĐƯA APP LÊN WEB (chọn 1 cách)
--------------------------------------------------

Cách A — Netlify Drop (nhanh nhất, nên làm trên máy tính)
  1. Giải nén file zip, được thư mục "quay-doi".
  2. Mở https://app.netlify.com/drop
  3. Kéo cả thư mục "quay-doi" thả vào trang.
  4. Đăng nhập / tạo tài khoản miễn phí khi được hỏi
     (để link không bị xóa).
  5. Được một link dạng https://ten-gi-do.netlify.app
     -> đổi tên cho dễ nhớ trong Site settings nếu muốn.

Cách B — GitHub Pages (nếu đã có tài khoản GitHub)
  1. Tạo repository mới, ví dụ "quay-doi".
  2. Add file -> Upload files -> chọn toàn bộ file trong thư mục.
  3. Settings -> Pages -> Source: "Deploy from a branch",
     Branch: main, thư mục / (root) -> Save.
  4. Sau 1–2 phút có link https://<tên-bạn>.github.io/quay-doi/

--------------------------------------------------
BƯỚC 2 — CÀI VÀO ĐIỆN THOẠI
--------------------------------------------------

Android:
  Mở link bằng Chrome -> bấm ⋮ -> "Cài đặt ứng dụng"
  (hoặc "Thêm vào màn hình chính").
  Trong app, tab Cài đặt cũng có nút "Cài app ngay".

iPhone:
  Mở link bằng Safari -> nút Chia sẻ -> "Thêm vào MH chính" -> Thêm.

Sau khi cài: mở app từ biểu tượng "Quay Đội". Từ đó trở đi chạy
offline hoàn toàn, không cần mạng.

--------------------------------------------------
CHUYỂN DỮ LIỆU TỪ BẢN CŨ (file HTML trước đây)
--------------------------------------------------
  1. Mở bản cũ -> tab Sao lưu -> "Sao chép mã sao lưu".
  2. Mở app mới -> tab Cài đặt -> "Khôi phục từ mã" -> dán -> Khôi phục.
  Người chơi, đội, tên trong game và lịch sử tỉ số được chuyển sang.

--------------------------------------------------
CẬP NHẬT PHIÊN BẢN MỚI
--------------------------------------------------
  Thay các file trên host bằng bản mới (Netlify: kéo thả lại vào
  mục Deploys; GitHub: upload đè). App trên điện thoại tự cập nhật
  ở lần mở thứ hai sau đó. Dữ liệu không bị mất.

--------------------------------------------------
LƯU Ý
--------------------------------------------------
- Dữ liệu chỉ nằm trên điện thoại của bạn, không gửi đi đâu.
- Nên "Tải file sao lưu" sau mỗi buổi đá (tab Cài đặt).
- Vẫn có thể mở trực tiếp index.html để dùng offline, nhưng cách đó
  không cài thành app được.
""" % VERSION

def main():
    if os.path.exists(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)
    html = open(SRC, encoding='utf-8').read()
    assert '/*FONTS*/' in html
    html = html.replace('/*FONTS*/', font_css(), 1)
    open(os.path.join(DIST, 'index.html'), 'w', encoding='utf-8').write(html)
    open(os.path.join(DIST, 'manifest.webmanifest'), 'w', encoding='utf-8').write(json.dumps(MANIFEST, ensure_ascii=False, indent=2))
    open(os.path.join(DIST, 'sw.js'), 'w', encoding='utf-8').write(SW)
    open(os.path.join(DIST, 'HUONG-DAN-CAI-DAT.txt'), 'w', encoding='utf-8').write(GUIDE)
    print('built', DIST, os.path.getsize(os.path.join(DIST, 'index.html')), 'bytes')

if __name__ == '__main__':
    main()
