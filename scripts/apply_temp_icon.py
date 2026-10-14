import base64
from PIL import Image

def main():
    # 1. Base64 encode for SVG
    with open('temp/icon.png', 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('utf-8')

    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <image href="data:image/png;base64,{b64}" width="512" height="512" />
</svg>
'''
    with open('web/plansggw.svg', 'w', encoding='utf-8') as f:
        f.write(svg_content)
    print("Updated web/plansggw.svg")

    # 2. Generate favicon.ico
    img = Image.open('temp/icon.png')
    img.save('web/favicon.ico', format='ICO', sizes=[(16, 16), (32, 32), (48, 48)])
    print("Generated web/favicon.ico")

if __name__ == '__main__':
    main()
