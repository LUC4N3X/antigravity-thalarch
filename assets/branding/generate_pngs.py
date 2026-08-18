import subprocess
import os
import tempfile

def render_svg_to_png(svg_path, png_path, width, height):
    msedge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(msedge_path):
        print(f"Edge not found at {msedge_path}")
        return
        
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        html_path = f.name
        f.write(f"""<!DOCTYPE html>
<html>
<head>
<style>
body {{ margin: 0; padding: 0; background: #060911; width: {width}px; height: {height}px; overflow: hidden; }}
</style>
</head>
<body>
  <img src="file:///{svg_path.replace(chr(92), '/')}" style="width: 100%; height: 100%; display: block;" />
</body>
</html>
""")
        
    cmd = [
        msedge_path,
        "--headless",
        f"--screenshot={png_path}",
        f"--window-size={width},{height}",
        f"file:///{html_path.replace(chr(92), '/')}"
    ]
    print(f"Rendering {png_path}...")
    subprocess.run(cmd, shell=True)
    os.remove(html_path)

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    render_svg_to_png(os.path.join(base_dir, "thalarch-icon.svg"), os.path.join(base_dir, "thalarch-icon.png"), 512, 512)
    render_svg_to_png(os.path.join(base_dir, "thalarch-logo.svg"), os.path.join(base_dir, "thalarch-logo.png"), 1200, 320)
    render_svg_to_png(os.path.join(base_dir, "thalarch-banner.svg"), os.path.join(base_dir, "thalarch-banner.png"), 1200, 340)
    print("Done!")
