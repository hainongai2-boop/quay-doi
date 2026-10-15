"""Bấm thử tự động mọi nút đang hiện ở mọi trạng thái của Quay Đội, báo nút nào không có tác dụng."""
import sys, json
from playwright.sync_api import sync_playwright
URL = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8765/'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'audit.json'
KEY = 'quaydoi-v3'
STUB = r"""
window.__ev=[];
navigator.share=function(){window.__ev.push('share');return Promise.resolve();};
navigator.canShare=function(){return true;};
try{Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:function(){window.__ev.push('clipboard');return Promise.resolve();}}});}catch(e){}
window.confirm=function(m){window.__ev.push('confirm');return true;};
(function(){var o=HTMLAnchorElement.prototype.click;HTMLAnchorElement.prototype.click=function(){if(this.download){window.__ev.push('download:'+this.download.split('-')[2]);return;}return o.call(this);};})();
(function(){var o=HTMLInputElement.prototype.click;HTMLInputElement.prototype.click=function(){if(this.type==='file'){window.__ev.push('filepicker');return;}return o.call(this);};})();
"""
TAG = r"""()=>{
  const modal=document.getElementById('modal'); const inModal=!modal.hidden;
  const root=inModal?modal:document;
  const sel='button, label.sw, .tnm, .mb, .chip';
  const out=[];
  root.querySelectorAll(sel).forEach(e=>{
    if(!inModal && e.closest('#modal')) return;
    if(e.closest('[hidden]')) return;
    const r=e.getBoundingClientRect(); if(r.width<=0||r.height<=0) return;
    if(e.closest('#toast')) return;
    if(e.closest('#tlist')){const rows=[...document.querySelectorAll('#tlist .trow')];if(rows.indexOf(e.closest('.trow'))>2)return;}
    const i=out.length; e.setAttribute('data-audit',i);
    const txt=(e.innerText||e.getAttribute('aria-label')||'').replace(/\s+/g,' ').trim().slice(0,46);
    const where=e.closest('section')?e.closest('section').id:(e.closest('nav')?'nav':(inModal?'modal':'?'));
    out.push({i, txt, where, disabled: !!e.disabled, cls: e.className});
  });
  return out;
}"""
SNAP = r"""()=>({pul:[...document.querySelectorAll('.pulse')].length+':'+[...document.querySelectorAll('.pulse')].map(e=>e.offsetTop).join(','),ls:localStorage.getItem('quaydoi-v3'), text:document.body.innerText, modal:!document.getElementById('modal').hidden,
  mhtml:document.getElementById('modal').innerHTML.length, toast:document.getElementById('toast').className.includes('show')?document.getElementById('toast').innerText:'',
  ev:window.__ev.slice(), y:window.scrollY, focus:document.activeElement?document.activeElement.id:''})"""

def run():
    res = {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={'width': 390, 'height': 844}, service_workers='block')
        ctx.add_init_script(STUB)
        pg = ctx.new_page()
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))

        def load(state):
            pg.goto(URL + '?blank')
            pg.evaluate("(s)=>{localStorage.clear(); if(s) localStorage.setItem('quaydoi-v3', s);}", state)
            pg.goto(URL); pg.wait_for_timeout(250)

        def ls(): return pg.evaluate(f"()=>localStorage.getItem('{KEY}')")
        def spin(i):
            pg.click(f'[data-spin="{i}"]'); pg.wait_for_timeout(2150)

        # ---- dựng các trạng thái mẫu ----
        load(None)
        snaps = {'onboarding': None}
        pg.fill('#ob0', 'Tuấn'); pg.fill('#ob1', 'Nam'); pg.click('#obGo')
        for k in range(2):
            spin(0); spin(1); pg.click('[data-st="0,1"]'); pg.click('#saveBtn'); pg.click('[data-act="new"]')
        snaps['idle'] = ls()
        spin(0); snaps['half'] = ls()
        spin(1); pg.click('[data-st="0,1"]'); snaps['play'] = ls()
        pg.click('#saveBtn'); snaps['done'] = ls()
        pg.click('[data-act="edit"]'); snaps['edit'] = ls()

        PREP = {
            'onboarding': ('onboarding', []),
            'idle': ('idle', []), 'half': ('half', []), 'play': ('play', []), 'edit': ('edit', []), 'done': ('done', []),
            'tab Thống kê': ('done', ['[data-tab="hist"]']),
            'tab Đội': ('idle', ['[data-tab="teams"]']),
            'tab Đội · đang sửa tên đội': ('idle', ['[data-tab="teams"]', '#tlist .tnm']),
            'tab Cài đặt': ('done', ['[data-tab="set"]']),
            'tab Cài đặt · mở dán mã': ('done', ['[data-tab="set"]', '#bkPasteToggle']),
            'modal Người chơi (ngoài trận)': ('idle', ['#p0 .pname']),
            'modal Người chơi (giữa trận)': ('play', ['#p0 .pname']),
            'modal Poster trận': ('done', ['[data-act="poster"]']),
            'modal Reset toàn bộ': ('done', ['[data-tab="set"]', '#resetAll']),
            'modal Poster buổi': ('done', ['[data-tab="hist"]', '#sessBox [data-sposter]']),
            'idle · đã tắt hết đội': ('idle', ['[data-tab="teams"]', '#allOff', '[data-tab="spin"]']),
            'play · tab Đội lọc đúng đội đang đá': ('play', ['[data-tab="teams"]', "js:()=>{const S=JSON.parse(localStorage.getItem('quaydoi-v3'));const t=S.teams.find(x=>x.id===S.cur.t[0]);const i=document.getElementById('tq');i.value=t.n;i.dispatchEvent(new Event('input'));}"]),
        }
        for name, (base, steps) in PREP.items():
            def prep():
                load(snaps[base])
                for s in steps:
                    if s.startswith('js:'): pg.evaluate(s[3:])
                    else: pg.click(s)
                    pg.wait_for_timeout(250)
                if 'Poster' in name: pg.wait_for_timeout(700)
            prep()
            items = pg.evaluate(TAG)
            rows = []
            for it in items:
                if it['disabled']:
                    rows.append({**it, 'effect': ['(đang mờ — không bấm được)']}); continue
                prep(); pg.evaluate(TAG)
                before = pg.evaluate(SNAP)
                try:
                    pg.click(f'[data-audit="{it["i"]}"]', timeout=2500)
                except Exception as e:
                    rows.append({**it, 'effect': ['LỖI BẤM: ' + str(e).split('\n')[0][:80]]}); continue
                pg.wait_for_timeout(350)
                if 'ĐANG QUAY' in pg.evaluate("()=>document.body.innerText"): pg.wait_for_timeout(2300)
                after = pg.evaluate(SNAP)
                eff = []
                if after['ls'] != before['ls']: eff.append('dữ liệu đổi')
                if after['modal'] != before['modal']: eff.append('mở bảng' if after['modal'] else 'đóng bảng')
                elif after['mhtml'] != before['mhtml']: eff.append('nội dung bảng đổi')
                if after['toast'] and after['toast'] != before['toast']: eff.append('thông báo: ' + after['toast'].replace('Hoàn tác', '').strip()[:50])
                newev = after['ev'][len(before['ev']):]
                eff += ['gọi ' + e for e in newev]
                if after['text'] != before['text'] and not any(x in eff for x in ('dữ liệu đổi',)): eff.append('giao diện đổi')
                if after['pul'] != before['pul']: eff.append('nháy nhẹ (đang chọn)')
                rows.append({**it, 'effect': eff or ['KHÔNG TÁC DỤNG']})
            res[name] = rows
        res['_errors'] = errs
        b.close()
    json.dump(res, open(OUT, 'w'), ensure_ascii=False, indent=1)
    bad = 0
    for st, rows in res.items():
        if st.startswith('_'): continue
        print(f'\n== {st} ({len(rows)} phần tử)')
        for r in rows:
            mark = '  ' if r['effect'][0] not in ('KHÔNG TÁC DỤNG',) and not r['effect'][0].startswith('LỖI') else '!!'
            if mark == '!!': bad += 1
            print(f"{mark} [{r['where']}] {r['txt'] or r['cls'][:30]!s:46} → {', '.join(r['effect'])}")
    print('\nJS errors:', res['_errors'])
    print('Tổng nút không tác dụng / lỗi:', bad)

run()
