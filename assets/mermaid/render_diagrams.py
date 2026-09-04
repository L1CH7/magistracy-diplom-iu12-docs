#!/usr/bin/env python3
import os
import sys
import glob
import time
import base64
import shutil
import subprocess
import urllib.request
import urllib.error

def render_diagrams():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mmd_dir = os.path.join(script_dir, "mmd")
    svg_dir = os.path.join(script_dir, "svg")
    png_dir = os.path.join(script_dir, "png")
    
    os.makedirs(svg_dir, exist_ok=True)
    os.makedirs(png_dir, exist_ok=True)
    
    mmd_files = sorted(glob.glob(os.path.join(mmd_dir, "*.mmd")))
    if not mmd_files:
        print(f"[-] No .mmd files found in {mmd_dir}")
        return
        
    print(f"[*] Found {len(mmd_files)} diagram(s) in {mmd_dir}")
    
    mmdc_path = shutil.which("mmdc")
    if not mmdc_path:
        candidate = os.path.abspath(os.path.join(script_dir, "..", "..", "latex-iu1-template", ".nodeenv", "bin", "mmdc"))
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            mmdc_path = candidate
            
    for mmd_path in mmd_files:
        basename = os.path.splitext(os.path.basename(mmd_path))[0]
        svg_out = os.path.join(svg_dir, f"{basename}.svg")
        png_out = os.path.join(png_dir, f"{basename}.png")
        
        print(f"[*] Processing {basename}...")
        rendered = False
        
        if mmdc_path:
            try:
                cmd = [mmdc_path, "-i", mmd_path, "-o", svg_out, "-b", "white"]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
                if res.returncode == 0 and os.path.exists(svg_out):
                    print(f"  [+] Rendered SVG via local mmdc: {svg_out}")
                    rendered = True
            except Exception as e:
                print(f"  [!] Local mmdc failed: {e}")
                
        if not rendered:
            with open(mmd_path, "r", encoding="utf-8") as f:
                content = f.read()
            b64 = base64.urlsafe_b64encode(content.encode("utf-8")).decode("ascii").rstrip("=")
            
            # Fetch SVG
            for attempt in range(3):
                try:
                    url_svg = f"https://mermaid.ink/svg/{b64}"
                    req_svg = urllib.request.Request(url_svg, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req_svg, timeout=15) as resp:
                        svg_data = resp.read()
                    with open(svg_out, "wb") as f:
                        f.write(svg_data)
                    print(f"  [+] Rendered SVG: {svg_out} ({len(svg_data)} bytes)")
                    rendered = True
                    break
                except Exception as e:
                    print(f"  [!] SVG attempt {attempt+1} failed ({e}), retrying...")
                    time.sleep(1.5)
                    
            # Fetch PNG for Word/DOCX
            if rendered:
                for attempt in range(2):
                    try:
                        url_png = f"https://mermaid.ink/img/{b64}?bgColor=white"
                        req_png = urllib.request.Request(url_png, headers={"User-Agent": "Mozilla/5.0"})
                        with urllib.request.urlopen(req_png, timeout=15) as resp:
                            png_data = resp.read()
                        with open(png_out, "wb") as f:
                            f.write(png_data)
                        print(f"  [+] Rendered PNG (for DOCX): {png_out} ({len(png_data)} bytes)")
                        break
                    except Exception as e:
                        time.sleep(1.5)

if __name__ == "__main__":
    render_diagrams()
