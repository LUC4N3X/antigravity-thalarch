import subprocess
import os

def render_svg_to_png(svg_path, png_path, width, height):
    msedge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not os.path.exists(msedge_path):
        print(f"Edge not found at {msedge_path}")
        return
        
    cmd = [
        msedge_path,
        "--headless",
        f"--screenshot={png_path}",
        f"--window-size={width},{height}",
        f"file:///{svg_path.replace(chr(92), '/')}"
    ]
    print(f"Rendering {png_path}...")
    subprocess.run(cmd, shell=True)

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    render_svg_to_png(os.path.join(base_dir, "thalarch-icon.svg"), os.path.join(base_dir, "thalarch-icon.png"), 1024, 1024)
    render_svg_to_png(os.path.join(base_dir, "thalarch-logo.svg"), os.path.join(base_dir, "thalarch-logo.png"), 1200, 320)
    render_svg_to_png(os.path.join(base_dir, "thalarch-banner.svg"), os.path.join(base_dir, "thalarch-banner.png"), 1280, 440)
    print("Done!")
