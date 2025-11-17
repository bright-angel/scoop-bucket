import requests
import json
import PySimpleGUI as sg
import re
from datetime import datetime

def get_github_info(repo_url):
    """获取 GitHub 项目信息"""
    try:
        # 提取 owner 和 repo
        match = re.match(r'https://github\.com/([^/]+)/([^/]+)', repo_url)
        if not match:
            return None, "无效的 GitHub URL"

        owner, repo = match.groups()

        # API 基础 URL
        base_url = f"https://api.github.com/repos/{owner}/{repo}"

        # 获取项目基本信息
        response = requests.get(base_url)
        if response.status_code != 200:
            return None, f"无法获取项目信息: {response.status_code}"

        repo_info = response.json()

        # 检查 repo_info 是否为 None
        if repo_info is None:
            return None, "项目信息为空"

        # 检查是否有错误消息
        if 'message' in repo_info:
            return None, f"错误: {repo_info['message']}"

        # 获取 releases
        releases_url = f"{base_url}/releases"
        releases_response = requests.get(releases_url)
        releases = releases_response.json() if releases_response.status_code == 200 else []

        # 获取 README
        readme_url = f"{base_url}/readme"
        readme_response = requests.get(readme_url)
        readme_content = ""
        if readme_response.status_code == 200:
            readme_data = readme_response.json()
            readme_content = readme_data.get('content', '')
            # 如果是 base64 编码，需要解码
            if readme_content:
                import base64
                try:
                    readme_content = base64.b64decode(readme_content).decode('utf-8')
                except:
                    readme_content = "无法解码 README 内容"

        # 获取最新 commit（用于无 release 的情况）
        commits_url = f"{base_url}/commits"
        commits_response = requests.get(commits_url)
        commits = commits_response.json() if commits_response.status_code == 200 else []
        latest_commit = commits[0] if commits else None

        # 获取最新 commit 的时间戳
        latest_commit_date = None
        if latest_commit:
            commit_date_str = latest_commit['commit']['committer']['date']
            # 将日期字符串转换为版本号格式
            match = re.match(r'([\d-]+)T(\d+):(\d+):(\d+)', commit_date_str)
            if match:
                date_part = match.group(1)
                hour = match.group(2)
                minute = match.group(3)
                second = match.group(4)
                latest_commit_date = f"{date_part}T{hour}.{minute}.{second}"

        # 安全地获取 license 信息
        license_info = "UNKNOWN"
        if repo_info.get('license'):
            license_info = repo_info['license'].get('name', 'UNKNOWN')

        # 安全地获取 homepage，如果为 None 则使用 repo_url
        homepage_info = repo_info.get('homepage')
        if not homepage_info:
            homepage_info = repo_url

        info = {
            'description': repo_info.get('description', ''),
            'homepage': homepage_info,
            'license': license_info,
            'has_releases': len(releases) > 0,
            'releases': releases,
            'readme': readme_content,
            'latest_commit': latest_commit,
            'latest_commit_date': latest_commit_date,
            'default_branch': repo_info.get('default_branch', 'master'),
            'repo_name': repo,
            'owner': owner
        }

        return info, None

    except Exception as e:
        return None, f"获取信息失败: {str(e)}"

def detect_project_type(repo_info):
    """检测项目类型"""
    if not repo_info:
        return 'generic'

    readme_lower = repo_info.get('readme', '').lower()
    description_lower = repo_info.get('description', '').lower()

    if any(keyword in readme_lower + description_lower for keyword in ['python', 'pip install', 'requirements.txt']):
        return 'python'
    elif any(keyword in readme_lower + description_lower for keyword in ['java', 'jar', 'maven', 'gradle']):
        return 'java'
    elif any(keyword in readme_lower + description_lower for keyword in ['exe', 'executable', 'windows']):
        return 'exe'
    elif any(keyword in readme_lower + description_lower for keyword in ['gui', 'graphical', 'interface', 'desktop']):
        return 'gui'
    else:
        return 'generic'

def show_project_settings(repo_info, auto_detected_type, has_releases):
    """显示项目设置窗口"""
    layout = [
        [sg.Text('项目设置', font=('Arial', 14, 'bold'))],
        [sg.Text('自动检测类型:'), sg.Text(auto_detected_type.upper(), text_color='yellow')],
        [sg.Text('手动指定类型:')],
        [sg.Radio('Python', "PROJECT_TYPE", key='-TYPE_PYTHON-', default=auto_detected_type=='python')],
        [sg.Radio('Java', "PROJECT_TYPE", key='-TYPE_JAVA-', default=auto_detected_type=='java')],
        [sg.Radio('可执行文件 (EXE)', "PROJECT_TYPE", key='-TYPE_EXE-', default=auto_detected_type=='exe')],
        [sg.Radio('图形界面程序', "PROJECT_TYPE", key='-TYPE_GUI-', default=auto_detected_type=='gui')],
        [sg.Radio('通用类型', "PROJECT_TYPE", key='-TYPE_GENERIC-', default=auto_detected_type=='generic')],
        [sg.HorizontalSeparator()],
        [sg.Text('Releases 设置:')],
        [sg.Radio('使用 Releases (推荐)', "RELEASES_TYPE", key='-RELEASES_YES-', default=has_releases)],
        [sg.Radio('不使用 Releases (使用主分支)', "RELEASES_TYPE", key='-RELEASES_NO-', default=not has_releases)],
        [sg.HorizontalSeparator()],
        [sg.Text('其他选项:')],
        [sg.Checkbox('添加快捷方式', key='-ADD_SHORTCUTS-', default=False)],
        [sg.Button('确定'), sg.Button('取消')]
    ]

    window = sg.Window('项目设置', layout)

    result = {
        'project_type': auto_detected_type,
        'use_releases': has_releases,
        'add_shortcuts': False
    }

    while True:
        event, values = window.read()

        if event in (sg.WIN_CLOSED, '取消'):
            break
        elif event == '确定':
            # 确定项目类型
            if values['-TYPE_PYTHON-']:
                result['project_type'] = 'python'
            elif values['-TYPE_JAVA-']:
                result['project_type'] = 'java'
            elif values['-TYPE_EXE-']:
                result['project_type'] = 'exe'
            elif values['-TYPE_GUI-']:
                result['project_type'] = 'gui'
            elif values['-TYPE_GENERIC-']:
                result['project_type'] = 'generic'

            # 确定是否使用 releases
            result['use_releases'] = values['-RELEASES_YES-']

            # 其他选项
            result['add_shortcuts'] = values['-ADD_SHORTCUTS-']

            break

    window.close()
    return result

def show_shortcut_options(repo_name):
    """显示快捷方式选项窗口"""
    layout = [
        [sg.Text('快捷方式设置', font=('Arial', 12, 'bold'))],
        [sg.Text('快捷方式名称:'), sg.Input(key='-SHORTCUT_NAME-', default_text=repo_name, size=(30, 1))],
        [sg.Text('启动文件:'), sg.Input(key='-LAUNCH_FILE-', default_text=f"{repo_name}.bat", size=(30, 1))],
        [sg.Button('确定'), sg.Button('取消')]
    ]

    window = sg.Window('快捷方式设置', layout)

    result = {'shortcut_name': repo_name, 'launch_file': f"{repo_name}.bat"}

    while True:
        event, values = window.read()

        if event in (sg.WIN_CLOSED, '取消'):
            break
        elif event == '确定':
            result['shortcut_name'] = values['-SHORTCUT_NAME-'] or repo_name
            result['launch_file'] = values['-LAUNCH_FILE-'] or f"{repo_name}.bat"
            break

    window.close()
    return result

def generate_scoop_json(repo_url, repo_info, project_settings):
    """生成 Scoop JSON 配置"""
    if not repo_info:
        return {"error": "没有可用的项目信息"}

    match = re.match(r'https://github\.com/([^/]+)/([^/]+)', repo_url)
    if not match:
        return {"error": "无效的 GitHub URL"}

    owner, repo = match.groups()

    project_type = project_settings['project_type']
    use_releases = project_settings['use_releases'] and repo_info.get('has_releases', False)
    add_shortcuts = project_settings.get('add_shortcuts', False)

    base_json = {
        "version": "",
        "description": repo_info.get('description', ''),
        "homepage": repo_info.get('homepage', repo_url),
        "license": repo_info.get('license', 'UNKNOWN'),
        # "hash": "",
        "checkver": "github",
        "autoupdate": {}
    }

    # 添加快捷方式配置（如果适用）
    if add_shortcuts:
        shortcut_options = project_settings.get('shortcut_options', {})
        shortcut_name = shortcut_options.get('shortcut_name', repo)
        launch_file = shortcut_options.get('launch_file', f"{repo}.bat")

        base_json["shortcuts"] = [
            [launch_file, shortcut_name]
        ]

    # 处理有 releases 的情况
    if use_releases and repo_info.get('releases'):
        latest_release = repo_info['releases'][0]
        version = latest_release['tag_name'].lstrip('v')

        # 更新版本号
        base_json["version"] = version

        # 查找下载文件
        download_url = None
        asset_name = None

        for asset in latest_release.get('assets', []):
            if asset['name'].endswith('.zip') or asset['name'].endswith('.exe') or asset['name'].endswith('.jar'):
                download_url = asset['browser_download_url']
                asset_name = asset['name']
                break

        if download_url:
            # 根据文件类型设置不同的配置
            if asset_name.endswith('.zip'):
                base_json.update({
                    "url": download_url,
                    "extract_dir": f"{repo}-{version}",
                    "autoupdate": {
                        "url": f"https://github.com/{owner}/{repo}/releases/download/$version/{asset_name}",
                        "extract_dir": f"{repo}-$version"
                    }
                })

                # 如果是 Python 项目
                if project_type == 'python':
                    base_json.update({
                        "suggest": {"python": ["miniconda3"]},
                        "pre_install": [
                            f'Set-Content "$dir\\{repo}.bat" \'@pushd %~dp0',
                            '@call activate python3env',
                            f'@python "{repo}.py" %*',
                            '@popd\' -Encoding Ascii'
                        ],
                        "post_install": [
                            '& cmd /c "call activate python3env && pip install -r $dir\\requirements.txt"'
                        ],
                        "bin": f"{repo}.bat"
                    })
                else:
                    # 通用配置
                    base_json["bin"] = f"{repo}.exe"

            elif asset_name.endswith('.exe'):
                base_json.update({
                    "url": download_url,
                    "bin": asset_name,
                    "autoupdate": {
                        "url": f"#{asset_name}"
                    }
                })

            elif asset_name.endswith('.jar'):
                base_name = asset_name[:-4]  # 去掉 .jar 后缀
                base_json.update({
                    "suggest": {"JRE": ["sec/oraclejre8"]},
                    "url": download_url,
                    "pre_install": [
                        f'Set-Content "$dir\\{base_name}.bat" \'@pushd %~dp0',
                        '@call oraclejre8',
                        f'@start javaw.exe -jar "{asset_name}" %*',
                        '@popd\' -Encoding Ascii'
                    ],
                    "bin": f"{base_name}.bat",
                    "autoupdate": {
                        "url": f"https://github.com/{owner}/{repo}/releases/download/$version/{asset_name}"
                    }
                })

    # 处理无 releases 的情况
    else:
        version = repo_info.get('latest_commit_date', "0.0.0")
        default_branch = repo_info.get('default_branch', 'master')

        base_json.update({
            "version": version,
            "url": f"https://github.com/{owner}/{repo}/archive/refs/heads/{default_branch}.zip",
            "extract_dir": f"{repo}-{default_branch}",
            "checkver": {
                "url": f"https://api.github.com/repos/{owner}/{repo}/commits",
                "regex": "([\\d-]+T)(\\d+):(\\d+):(\\d+)",
                "replace": "$1$2.$3.$4"
            },
            "autoupdate": {
                "url": f"https://github.com/{owner}/{repo}/archive/refs/heads/{default_branch}.zip"
            }
        })

        # 根据项目类型添加特定配置
        if project_type == 'python':
            base_json.update({
                "suggest": {"python": ["miniconda3"]},
                "pre_install": [
                    f'Set-Content "$dir\\{repo}.bat" \'@pushd %~dp0',
                    '@call activate python3env',
                    f'@python "{repo}.py" %*',
                    '@popd\' -Encoding Ascii'
                ],
                "post_install": [
                    '& cmd /c "call activate python3env && pip install -r $dir\\requirements.txt"'
                ],
                "bin": f"{repo}.bat"
            })
        elif project_type == 'java':
            base_json.update({
                "suggest": {"JRE": ["sec/oraclejre8"]},
                "pre_install": [
                    f'Set-Content "$dir\\{repo}.bat" \'@pushd %~dp0',
                    '@call oraclejre8',
                    f'@start javaw.exe -jar "{repo}.jar" %*',
                    '@popd\' -Encoding Ascii'
                ],
                "bin": f"{repo}.bat"
            })
        else:
            base_json["bin"] = f"{repo}.exe"

    return base_json

def main():
    sg.theme('DarkBlue3')

    # 布局定义
    layout = [
        [sg.Text('GitHub 项目链接:'), sg.Input(key='-URL-', size=(50, 1))],
        [sg.Button('获取信息', key='-FETCH-'), sg.Button('生成 JSON', key='-GENERATE-'), sg.Button('退出')],
        [sg.HorizontalSeparator()],
        [sg.Text('项目信息:', font=('Arial', 12, 'bold'))],
        [sg.Multiline(key='-INFO-', size=(80, 10), autoscroll=True)],
        [sg.Text('自动检测类型:'), sg.Text('', key='-PROJECT_TYPE-', text_color='yellow')],
        [sg.Text('Releases 状态:'), sg.Text('', key='-RELEASES_STATUS-', text_color='yellow')],
        [sg.Text('最新 Commit 时间:'), sg.Text('', key='-COMMIT_DATE-', text_color='yellow')],
        [sg.HorizontalSeparator()],
        [sg.Text('Scoop JSON 配置:', font=('Arial', 12, 'bold'))],
        [sg.Multiline(key='-JSON-', size=(80, 20), autoscroll=True)],
        [sg.Button('复制到剪贴板', key='-COPY-'), sg.Button('保存到文件', key='-SAVE-')]
    ]

    window = sg.Window('Scoop 配置生成器', layout, finalize=True)

    repo_info = None
    current_json = None
    auto_detected_type = None

    while True:
        event, values = window.read()

        if event in (sg.WIN_CLOSED, '退出'):
            break

        elif event == '-FETCH-':
            url = values['-URL-'].strip()
            if not url:
                sg.popup_error('请输入 GitHub 项目链接')
                continue

            window['-INFO-'].update('正在获取项目信息...')
            window.refresh()

            repo_info, error = get_github_info(url)
            if error:
                sg.popup_error(f'错误: {error}')
                window['-INFO-'].update('')
                continue

            if not repo_info:
                sg.popup_error('无法获取项目信息')
                window['-INFO-'].update('')
                continue

            # 显示项目信息
            info_text = f"项目名称: {repo_info.get('repo_name', '未知')}\n"
            info_text += f"项目描述: {repo_info.get('description', '无描述')}\n"
            info_text += f"主页: {repo_info.get('homepage', '无主页')}\n"
            info_text += f"许可证: {repo_info.get('license', '未知')}\n"
            info_text += f"默认分支: {repo_info.get('default_branch', 'master')}\n"
            info_text += f"是否有 Releases: {repo_info.get('has_releases', False)}\n"

            if repo_info.get('has_releases') and repo_info.get('releases'):
                info_text += f"\n最新 Release: {repo_info['releases'][0]['tag_name']}\n"
                info_text += "Release 文件:\n"
                for asset in repo_info['releases'][0].get('assets', []):
                    info_text += f"  - {asset['name']} ({asset['size']} bytes)\n"

            info_text += f"\nREADME 长度: {len(repo_info.get('readme', ''))} 字符"

            window['-INFO-'].update(info_text)

            # 检测项目类型
            auto_detected_type = detect_project_type(repo_info)
            window['-PROJECT_TYPE-'].update(auto_detected_type.upper())

            # 显示 releases 状态
            releases_status = "有 Releases" if repo_info.get('has_releases', False) else "无 Releases"
            window['-RELEASES_STATUS-'].update(releases_status)

            # 显示最新 commit 时间
            commit_date = repo_info.get('latest_commit_date', "无法获取")
            window['-COMMIT_DATE-'].update(commit_date)

        elif event == '-GENERATE-':
            if not repo_info:
                sg.popup_error('请先获取项目信息')
                continue

            url = values['-URL-'].strip()

            # 显示项目设置窗口
            project_settings = show_project_settings(
                repo_info,
                auto_detected_type,
                repo_info.get('has_releases', False)
            )

            # 如果用户取消设置，跳过生成
            if not project_settings:
                continue

            # 如果需要添加快捷方式，获取快捷方式设置
            if project_settings.get('add_shortcuts', False):
                shortcut_options = show_shortcut_options(repo_info.get('repo_name', 'app'))
                project_settings['shortcut_options'] = shortcut_options

            current_json = generate_scoop_json(url, repo_info, project_settings)
            window['-JSON-'].update(json.dumps(current_json, indent=4, ensure_ascii=False))

        elif event == '-COPY-':
            if current_json:
                sg.clipboard_set(json.dumps(current_json, indent=4, ensure_ascii=False))
                sg.popup('已复制到剪贴板')
            else:
                sg.popup_error('没有可复制的 JSON 内容')

        elif event == '-SAVE-':
            if current_json:
                filename = sg.popup_get_file('保存文件', save_as=True, default_extension='.json')
                if filename:
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(current_json, f, indent=4, ensure_ascii=False)
                    sg.popup(f'已保存到: {filename}')
            else:
                sg.popup_error('没有可保存的 JSON 内容')

    window.close()

if __name__ == '__main__':
    main()
