from PIL import Image, ImageDraw
import threading

# generate a sample blueprint
def create_blueprint():
    img = Image.new('RGB', (1024, 1024), color='white')
    draw = ImageDraw.Draw(img)

    # 绘制房屋轮廓 (矩形)
    draw.rectangle([200, 300, 800, 800], outline='blue', width=5)

    # 绘制屋顶 (使用线条模拟多边形)
    draw.line([(200, 300), (500, 100)], fill='blue', width=5)  # 左边线
    draw.line([(800, 300), (500, 100)], fill='blue', width=5)  # 右边线

    # 绘制门 (矩形)
    draw.rectangle([450, 600, 550, 800], outline='blue', width=5)

    # 绘制窗户 (两个小矩形)
    draw.rectangle([250, 400, 350, 500], outline='blue', width=5)
    draw.rectangle([650, 400, 750, 500], outline='blue', width=5)

    return img


def show_image_non_blocking(image):
    def show_image():
        image.show()
    threading.Thread(target=show_image).start()

# save as jpg
def save_image_to_jpg(image):
    desktop_path = r'C:\Users\26681\Desktop\blueprint_output.jpg'
    image.save(desktop_path, 'JPEG')
    print(f"Blueprint saved as {desktop_path}")

# save as png
def save_image_to_png(image):
    desktop_path = r'C:\Users\26681\Desktop\blueprint_output.png'
    image.save(desktop_path, 'PNG')
    print(f"Blueprint saved as {desktop_path}")

# save as dxf
def save_image_to_dxf(image_data):
    desktop_path = r'C:\Users\26681\Desktop\blueprint_output.dxf'
    with open(desktop_path, 'w') as dxf_file:
        dxf_file.write("DXF data goes here")
    print(f"Blueprint saved as {desktop_path}")

# save as stl
def save_image_to_stl(mesh_data):
    desktop_path = r'C:\Users\26681\Desktop\blueprint_output.stl'
    with open(desktop_path, 'w') as stl_file:
        stl_file.write("STL data goes here")
    print(f"Blueprint saved as {desktop_path}")


def main():
    blueprint = create_blueprint()
    show_image_non_blocking(blueprint)

    while True:
        tp = input('Please input the type you want (jpg/png/dxf/stl). To stop, enter "n": ').strip().lower()

        if tp == 'jpg':
            save_image_to_jpg(blueprint)
        elif tp == 'png':
            save_image_to_png(blueprint)
        elif tp == 'dxf':
            save_image_to_dxf(blueprint)
        elif tp == 'stl':
            save_image_to_stl(blueprint)
        elif tp == 'n':
            print("Exiting the loop.")
            break
        else:
            print("Unsupported format. Please choose from jpg, png, dxf, stl, or enter 'n' to stop.")

if __name__ == "__main__":
    main()
