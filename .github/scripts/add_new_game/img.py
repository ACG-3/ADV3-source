import requests
from PIL import Image
import os
from io import BytesIO
import subprocess
import pillow_avif  # 确保导入pillow_avif插件

webdav_url = 'https://pan.timero.xyz/dav/onedrive/img_lib_001/'
webdav_username = os.getenv('WEBDAV_USERNAME')
webdav_password = os.getenv('WEBDAV_PASSWORD')

def upload_to_webdav(local_file_path):
    file_name = local_file_path.split('\\')[-1]
    # remote_file_path = f'onedrive/img_lib_001/{file_name}'
    command = f'curl -v -u {webdav_username}:{webdav_password} -T {local_file_path} {webdav_url}'
    try:
        subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        print("Upload successful.")
        return f"https://pan.timero.xyz/onedrive/img_lib_001/{file_name}"
    except subprocess.CalledProcessError as e:
        print("Error occurred:", e.output.decode())


def download_image(image_url):
    response = requests.get(image_url)
    if response.status_code == 200:
        return Image.open(BytesIO(response.content))
    else:
        raise Exception(f"Failed to download image from {image_url}")

def convert_image_to_avif(img, output_path):
    img.save(output_path, format='AVIF')

def upload_image_to_picgo(image_path):
    url = "http://127.0.0.1:36677/upload"
    payload = {"list": [image_path]}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200 and response.json().get("success"):
        return response.json().get("result")[0]
    else:
        raise Exception("Failed to upload image to picgo. Response: " + response.text)

def delete_local_image(image_path):
    if os.path.exists(image_path):
        os.remove(image_path)
    else:
        print(f"The file {image_path} does not exist.")

def process_single_image(image_url, game_title, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    try:
        # 下载图片
        img = download_image(image_url)
        # 构建输出路径，使用游戏标题和图片URL的一部分来创建唯一文件名
        filename = f"{game_title}_cover.avif"
        output_path = os.path.join(output_folder, filename)
        # 转换并保存为AVIF格式
        convert_image_to_avif(img, output_path)
        # 上传到图床
        new_url = upload_to_webdav(output_path)
        # 删除本地文件
        delete_local_image(output_path)
        print(f"Processed image {image_url}")
        return new_url
    except Exception as e:
        print(f"Error processing image {image_url}: {e}")
        return None


def process_images(screenshots, game_title, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    processed_screenshots = []
    for screenshot in screenshots:
        try:
            img = download_image(screenshot['url'])
            # 构建输出路径时使用标题创建唯一文件名
            output_path = os.path.join(output_folder, f"{game_title}_{screenshot['title'].replace(' ', '_')}.avif")
            convert_image_to_avif(img, output_path)
            new_url = upload_to_webdav(output_path)
            processed_screenshots.append({'title': screenshot['title'], 'url': new_url})
            delete_local_image(output_path)
            print(f"Processed image {screenshot['title']}")
        except Exception as e:
            print(f"Error processing image {screenshot['title']}: {e}")
            processed_screenshots.append({'title': screenshot['title'], 'url': 'Error processing image'})
    
    return processed_screenshots

# 示例调用
# screenshots = [
#     {'title': 'Screenshot 1', 'url': 'https://t.vndb.org/sf/48/71248.jpg'},
#     {'title': 'Screenshot 2', 'url': 'https://t.vndb.org/sf/49/71249.jpg'},
#     # 更多截图...
# ]

# game_title = "YourGameTitle"
# output_folder = r".\img"
# new_screenshots = process_images(screenshots, game_title, output_folder)
# print(new_screenshots)
