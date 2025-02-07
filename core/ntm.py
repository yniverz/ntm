import toml
import os
import platform
import subprocess
import requests
import os


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







os.environ['BASE_PATH'] = os.path.abspath(__file__).removesuffix(os.path.basename(__file__))

try:
    config = toml.load(os.environ['BASE_PATH'] + 'config.toml')
except FileNotFoundError:
    config = toml.load(os.environ['BASE_PATH'] + 'config.template.toml')

if config['type'] not in ['client', 'server']:
    raise ValueError('Invalid NTM type in config.toml')

install_latest_frp()


if config['type'] == 'client':
    subprocess.run([os.environ['BASE_PATH'] + 'bin/frp/frpc', '-c', os.environ['BASE_PATH'] + 'bin/frp/frpc.toml'])
else:
    subprocess.run([os.environ['BASE_PATH'] + 'bin/frp/frps', '-c', os.environ['BASE_PATH'] + 'bin/frp/frps.toml'])
