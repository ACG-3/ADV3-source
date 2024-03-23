import os
import requests
import random
import string
import deepl
import re
import urllib.parse
from jinja2 import Environment, FileSystemLoader
import json

from img import process_images, process_single_image

auth_key = os.getenv('DEEPL_AUTH_KEY')  # 你的 DeepL API Key

relation_map = {
    'orig': '原作',
    'fan': '外传',
    'set': '系列',
    'preq': '前作',
    'ser': '世界观',
    'seq': '续作',
    'char': '角色',
    'side': '旁支',
    'alt': '变体',
    'par': '核心',
    # 添加更多关系映射
}

def sanitize_file_name(name):
    # 移除 Windows 文件夹名中不允许的特殊字符
    return re.sub(r'[<>:"/\\|?*]', '', name)

def fetch_game_info_by_name(search_term):
    # API 请求
    url = 'https://api.vndb.org/kana/vn'  # 更新为正确的 API URL
    payload = {
        "filters": ["search", "=", search_term],
        "fields": "id,title,titles.lang,titles.title,titles.latin,aliases,released,languages,platforms,image.id,image.url,image.dims,image.sexual,image.violence,length,length_minutes,description,screenshots.thumbnail,screenshots.thumbnail_dims,relations.relation,developers.name,developers.original,developers.aliases,developers.lang,developers.type,developers.description,tags.name,tags.vn_count,released"
    }
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        raise Exception(f"API 请求失败，状态码: {response.status_code}")
    return response.json()

def fetch_game_info_by_id(game_id):
    # 请求相关作品的信息
    url = f'https://api.vndb.org/kana/vn'  # 更新为正确的 API URL
    payload = {
        "filters": ["id", "=", game_id],
        "fields": "id,title,titles.lang,titles.title,titles.latin,aliases,released,languages,platforms,image.id,image.url,image.dims,image.sexual,image.violence,length,length_minutes,description,screenshots.thumbnail,screenshots.thumbnail_dims,relations.relation,developers.name,developers.original,developers.aliases,developers.lang,developers.type,developers.description,tags.name,tags.vn_count,released"
    }
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        raise Exception(f"API 请求失败，状态码: {response.status_code}")
    return response.json()

def escape_double_quotes(s):
    return s.replace('"', '\"')

def fetch_game_title_jp(game_id):
    # 请求相关作品的信息
    url = f'https://api.vndb.org/kana/vn'  # 更新为正确的 API URL
    payload = {
        "filters": ["id", "=", game_id],
        "fields": "titles.title,titles.lang"
    }
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        raise Exception(f"API 请求失败，状态码: {response.status_code}")
    game_data = response.json()

    # 尝试找到日文标题
    title_jp = None
    fallback_title = None
    for title in game_data['results'][0]['titles']:
        if title['lang'] == 'ja':
            title_jp = title['title']
            break
        if fallback_title is None:
            fallback_title = title['title']
    
    return title_jp if title_jp else fallback_title


def clean_description(description):
    # 定义要移除的新文本模式的正则表达式
    pattern = r"(?i)\[.*?\[url=.*?\].*?\[/url\]\]"

    # 使用正则表达式替换掉匹配的文本
    cleaned_description = re.sub(pattern, '', description)

    return cleaned_description

def translate_text_with_deepl(text, auth_key):
    translator = deepl.Translator(auth_key)
    result = translator.translate_text(text, target_lang="ZH")
    return result.text

def create_markdown(data):
    # 配置 Jinja2 环境
    env = Environment(loader=FileSystemLoader(r'.github/scripts/add_new_game/templates'))
    template = env.get_template('game_template.md.j2')
    
    # 获取游戏描述并清理
    game_description = data['results'][0]['description'] if data['results'][0]['description'] else "暂无描述"
    cleaned_description = clean_description(game_description)
    # 翻译游戏简介
    translated_description = translate_text_with_deepl(cleaned_description, auth_key)
    # 提取相关作品的信息
    relations_info = data['results'][0]['relations']

    # 格式化相关作品的信息
    formatted_relations = ['']
    for relation in relations_info:
        game_id = relation['id']
        relation_type = relation['relation']
        # 获取日文名称
        title_jp = fetch_game_title_jp(game_id)
        # 转换关系为中文
        relation_cn = relation_map.get(relation_type, '未知关系')
        formatted_relations.append(f"   - {relation_cn}：{title_jp}")
    # 将格式化的相关作品信息转换为字符串
    relations_str = '\n'.join(formatted_relations)
    
    # 检查 'length_minutes' 是否存在，并且不是 None
    if 'length_minutes' in data['results'][0] and data['results'][0]['length_minutes'] is not None:
        game_length = round(data['results'][0]['length_minutes'] / 60, 2)
    else:
        game_length = "none"
        
    # 提取游戏标题，优先使用日文名，如果没有，则使用API回复中的"title"
    game_title_jp = next((title['title'] for title in data['results'][0]['titles'] if title['lang'] == 'ja'), None)
    game_title = game_title_jp if game_title_jp != None else data['results'][0]['title']
    clean_game_title = escape_double_quotes(game_title)
    
    file_name = sanitize_file_name(game_title)
    
    global download_link, download_password, unpack_password, download_platform
    # 准备数据（根据实际 API 返回的数据结构调整）
    game_data = {
        'game_title_url': urllib.parse.quote(file_name),
        'game_release_date': data['results'][0]['released'],
        'game_title': clean_game_title,
        'game_cover': process_single_image(data['results'][0]['image']['url'], file_name, img_folder_path),
        'game_title_jp': next((title['title'] for title in data['results'][0]['titles'] if title['lang'] == 'ja'), None),
        'game_title_en': next((title['title'] for title in data['results'][0]['titles'] if title['lang'] == 'en'), None),
        'game_title_cn': next((title['title'] for title in data['results'][0]['titles'] if title['lang'] == 'zh-Hans'), None),
        'game_title_alias': ', '.join(data['results'][0]['aliases']),
        'game_length': game_length,
        'game_developer': ', '.join([dev['name'] for dev in data['results'][0]['developers']]),
        'game_platform': ', '.join(data['results'][0]['platforms']),
        'game_related_works': relations_str,
        'game_related_links': '暂无',  # 你可以根据需要添加链接
        'game_description': translated_description,
        'game_vndb_id': data['results'][0]['id'],
        'screenshots': process_images([{'title': f'Screenshot {i+1}', 'url': sc['thumbnail'].replace('st', 'sf')} for i, sc in enumerate(data['results'][0]['screenshots'][:5])], file_name, img_folder_path),
        'download_link': download_link,  # 这里添加下载链接
        'download_password': download_password,  # 这里添加下载链接的提取码
        'unpack_password': unpack_password,  # 这里添加解压密码
    }   

    # 生成 Markdown 内容
    md_content = template.render(game_data)

    # file_name = sanitize_file_name(game_title)

    # 保存 Markdown 文件
    with open(os.path.join(md_folder_path, file_name + ".md"), 'w', encoding='utf-8') as file:
        file.write(md_content)

    print (os.path.join(md_folder_path, file_name + ".md"))
    
def get_issue_content(issue_number):
    # 替换为你的 GitHub 仓库信息
    repo_owner = 'ACG-3'
    repo_name = 'ADV3-source'
    token = os.getenv('GITHUB_TOKEN')

    headers = {
        # 'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{issue_number}'
    response = requests.get(url, headers=headers)
    issue = response.json()
    return issue['body']

issue_map = {
    '游戏原名': 'game_name',
    'VNDB ID': 'vndb_id',
    '下载链接': 'download_link',
    '下载方式': 'download_paltform',
    '解压密码': 'unpack_password',
    '下载密码': 'download_password'
}

def get_issue_number():
    event_path = os.getenv('GITHUB_EVENT_PATH')
    with open(event_path) as event_file:
        event_data = json.load(event_file)
        return event_data['issue']['number']


def parse_issue_body(issue_body):
    lines = issue_body.split('\n\n')
    data = {}
    for i in range(0, len(lines) / 2, 2):
        key = issue_map.get(lines[i].strip("#").strip())
        value = lines[i + 1].strip()
        data[key] = value
    return data

md_folder_path = 'source/_posts/games'
img_folder_path = '.github/scripts/add_new_game/img'

def main():
    issue_number = get_issue_number()
    # issue_number = 8
    issue_body = get_issue_content(issue_number)
    issue_data = parse_issue_body(issue_body)
    global download_link
    download_link = issue_data['download_link']
    global download_password
    download_password = issue_data['download_password']
    global unpack_password
    unpack_password = issue_data['unpack_password']
    global download_platform
    download_platform = issue_data['download_paltform']
    if 'vndb_id' in issue_data:
        game_id = issue_data['vndb_id']
        game_data = fetch_game_info_by_id(game_id)
        create_markdown(game_data)
    else:
        search_term = issue_data['game_name']
        game_data = fetch_game_info_by_name(search_term)
        create_markdown(game_data)
        
main()