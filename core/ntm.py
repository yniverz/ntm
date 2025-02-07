import time
import traceback
import toml
import os
import platform
import subprocess
import requests

def get_github_latest_release_info(user, repo):
    url = f"https://api.github.com/repos/{user}/{repo}/releases/latest"
    response = requests.get(url)
    return response.json()

def get_latest_frp_download_link():
    release = get_github_latest_release_info("fatedier", "frp")

    system = platform.system()
    if system in ["Linux"]:
        if platform.machine().lower() == "x86_64":
            asset_type = "linux_amd64"
        elif platform.machine().lower() == "arm64":
            asset_type = "arm"
        else:
            raise Exception("Unsupported architecture")
    else:
        raise Exception("Unsupported platform")
    
    asset = next(asset for asset in release["assets"] if asset_type in str(asset["name"]))

    return asset["browser_download_url"], asset["name"]

def download_latest_frp():
    url, filename = get_latest_frp_download_link()
    response = requests.get(url)
    with open(os.environ['BASE_PATH'] + filename, "wb") as file:
        file.write(response.content)

    return filename

def install_latest_frp():
    filename = download_latest_frp()
    subprocess.run(["tar", "-xvf", os.environ['BASE_PATH'] + filename, "-C", os.environ['BASE_PATH']])
    subprocess.run(["mkdir", "-p", os.environ['BASE_PATH'] + "bin"])
    subprocess.run(["rm", "-rf", os.environ['BASE_PATH'] + "bin/frp"])
    subprocess.run(["mv", os.environ['BASE_PATH'] + filename.replace(".tar.gz", ""), os.environ['BASE_PATH'] + "bin/frp"])
    subprocess.run(["rm", os.environ['BASE_PATH'] + filename])

    if not os.path.exists(os.environ['BASE_PATH'] + 'bin/frpc.toml'):
        subprocess.run(["mv", os.environ['BASE_PATH'] + 'bin/frp/frpc.toml', os.environ['BASE_PATH'] + 'bin/frpc.toml'])

    if not os.path.exists(os.environ['BASE_PATH'] + 'bin/frps.toml'):
        subprocess.run(["mv", os.environ['BASE_PATH'] + 'bin/frp/frps.toml', os.environ['BASE_PATH'] + 'bin/frps.toml'])









os.environ['BASE_PATH'] = os.path.abspath(__file__).removesuffix(os.path.basename(__file__))

config = toml.load(os.environ['BASE_PATH'] + '../config.toml')

if config['type'] not in ['client', 'server']:
    raise ValueError('Invalid NTM type in config.toml')

install_latest_frp()

while True:
    try:
        if config['type'] == 'client':
            subprocess.run([os.environ['BASE_PATH'] + 'bin/frp/frpc', '-c', os.environ['BASE_PATH'] + '../frpc.toml'])
        else:
            subprocess.run([os.environ['BASE_PATH'] + 'bin/frp/frps', '-c', os.environ['BASE_PATH'] + '../frps.toml'])

    except Exception as e:
        print(traceback.format_exc())

    print("Restarting in 5 seconds...")

    time.sleep(5)
