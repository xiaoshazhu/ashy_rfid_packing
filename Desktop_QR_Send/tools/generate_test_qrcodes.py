"""使用 Python 官方 qrcode 库生成真正的标准二维码 PNG 图片并嵌入 HTML

解决浏览器中原生动态算法生成的二维码无法被摄像头扫描识别的问题。
"""

import base64
import os
from io import BytesIO
from pathlib import Path

try:
    import qrcode
except ImportError:
    os.system("python -m pip install qrcode pillow")
    import qrcode


def generate_qr_base64(text: str) -> str:
    """生成标准 QRCode 的 base64 DataURI 字符串"""
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_str}"


def build_html_with_standard_qrcodes():
    total_bundles = 10
    boxes_per_bundle = 10

    print("正在使用 Python qrcode 官方渲染引擎为您批量生成 100 盒二维码，请稍候...")
    
    # 提前生成所有二维码 base64 数据
    bundle_data = {}
    for bundle in range(1, total_bundles + 1):
        bundle_data[bundle] = []
        for box in range(1, boxes_per_bundle + 1):
            pad_bundle = str(bundle).zfill(2)
            pad_box = str(box).zfill(2)
            code_str = f"YK20268899{pad_bundle}{pad_box}001"
            b64_img = generate_qr_base64(code_str)
            bundle_data[bundle].append({
                "title": f"第 {bundle} 捆 - 第 {box} 盒",
                "code": code_str,
                "b64": b64_img
            })

    # 生成重复测试区数据（使用第 1 捆）
    dup_data = []
    for box in range(1, boxes_per_bundle + 1):
        pad_box = str(box).zfill(2)
        code_str = f"YK2026889901{pad_box}001"
        b64_img = generate_qr_base64(code_str)
        dup_data.append({
            "title": f"第 1 捆 - 第 {box} 盒 (已扫重复项)",
            "code": code_str,
            "b64": b64_img
        })

    import json
    bundle_json = json.dumps(bundle_data, ensure_ascii=False)
    dup_json = json.dumps(dup_data, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>激光扫码装箱 - 100盒离线高清测试卡</title>
    <style>
        * {{ box-sizing: border-box; font-family: "PingFang SC", "Microsoft YaHei", sans-serif; }}
        body {{ background-color: #F1F5F9; margin: 0; padding: 20px; color: #1E293B; }}
        .header {{ background: #FFFFFF; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 20px; }}
        h1 {{ margin: 0 0 10px 0; color: #0F172A; font-size: 24px; }}
        p {{ margin: 0; color: #64748B; font-size: 14px; line-height: 1.5; }}
        
        .tabs {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px; }}
        .tab-btn {{ background: #FFFFFF; border: 1px solid #CBD5E1; padding: 10px 16px; border-radius: 8px; cursor: pointer; font-weight: bold; color: #475569; transition: all 0.2s; }}
        .tab-btn:hover {{ background: #E2E8F0; }}
        .tab-btn.active {{ background: #2563EB; color: #FFFFFF; border-color: #2563EB; box-shadow: 0 2px 6px rgba(37,99,235,0.3); }}
        .tab-btn.dup-btn {{ background: #FEF2F2; color: #DC2626; border-color: #FCA5A5; }}
        .tab-btn.dup-btn.active {{ background: #DC2626; color: #FFFFFF; border-color: #DC2626; }}
        
        .grid-container {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; background: #FFFFFF; padding: 24px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }}
        .qr-card {{ border: 2px solid #E2E8F0; border-radius: 8px; padding: 12px; text-align: center; background: #FAFAFA; transition: transform 0.2s; }}
        .qr-card:hover {{ transform: translateY(-2px); border-color: #3B82F6; }}
        .qr-title {{ font-weight: bold; font-size: 16px; color: #1E293B; margin-bottom: 8px; }}
        .qr-code-box {{ width: 150px; height: 150px; margin: 0 auto 8px auto; background: #FFFFFF; display: flex; align-items: center; justify-content: center; border: 1px solid #E2E8F0; border-radius: 4px; padding: 4px; }}
        .qr-code-box img {{ width: 100%; height: 100%; object-fit: contain; image-rendering: pixelated; }}
        .qr-text {{ font-size: 11px; color: #64748B; word-break: break-all; font-family: monospace; }}
        .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; background: #DBEAFE; color: #1D4ED8; margin-top: 4px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📦 激光扫码装箱 - 100盒离线高清测试卡</h1>
        <p>💡 <b>测试说明：</b> 本页面包含 100 个生成的真实标准二维码（共 10 捆，每捆 10 盒）。请将本页面显示在屏幕上，把摄像头对准屏幕即可精准测试去重、缺件补扫与整箱装配。</p>
    </div>

    <div class="tabs" id="tab-bar"></div>
    <div class="grid-container" id="qr-grid"></div>

    <script>
        const BUNDLE_DATA = {bundle_json};
        const DUP_DATA = {dup_json};
        let currentBundle = 1;

        function renderTabs() {{
            const tabBar = document.getElementById('tab-bar');
            tabBar.innerHTML = '';

            for (let i = 1; i <= 10; i++) {{
                const btn = document.createElement('button');
                btn.className = `tab-btn ${{i === currentBundle ? 'active' : ''}}`;
                btn.innerText = `第 ${{i}} 捆 (10盒)`;
                btn.onclick = () => switchBundle(i);
                tabBar.appendChild(btn);
            }}

            const dupBtn = document.createElement('button');
            dupBtn.className = `tab-btn dup-btn ${{currentBundle === 'dup' ? 'active' : ''}}`;
            dupBtn.innerText = `⚠️ 重复测试区 (已扫盒码)`;
            dupBtn.onclick = () => switchBundle('dup');
            tabBar.appendChild(dupBtn);
        }}

        function switchBundle(bundleIdx) {{
            currentBundle = bundleIdx;
            renderTabs();
            renderGrid();
        }}

        function renderGrid() {{
            const container = document.getElementById('qr-grid');
            container.innerHTML = '';
            const list = currentBundle === 'dup' ? DUP_DATA : BUNDLE_DATA[currentBundle];

            list.forEach(item => {{
                createCard(container, item.title, item.code, item.b64, currentBundle === 'dup');
            }});
        }}

        function createCard(parent, title, code, b64, isDup) {{
            const card = document.createElement('div');
            card.className = 'qr-card';

            const titleEl = document.createElement('div');
            titleEl.className = 'qr-title';
            titleEl.innerText = title;

            const qrBox = document.createElement('div');
            qrBox.className = 'qr-code-box';
            
            const img = document.createElement('img');
            img.src = b64;
            qrBox.appendChild(img);

            const textEl = document.createElement('div');
            textEl.className = 'qr-text';
            textEl.innerText = code;

            const badge = document.createElement('div');
            badge.className = 'badge';
            badge.innerText = isDup ? '已知重复盒码' : `唯一盒码`;
            if (isDup) badge.style.background = '#FEE2E2', badge.style.color = '#991B1B';

            card.appendChild(titleEl);
            card.appendChild(qrBox);
            card.appendChild(textEl);
            card.appendChild(badge);
            parent.appendChild(card);
        }}

        renderTabs();
        renderGrid();
    </script>
</body>
</html>
"""
    html_path = Path(__file__).resolve().parent / "qr_test_page.html"
    html_path.write_text(html_content, encoding="utf-8")
    print(f"SUCCESS: Generated standard QR test page at {html_path.absolute()}")

if __name__ == "__main__":
    build_html_with_standard_qrcodes()
