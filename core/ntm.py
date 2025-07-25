from dataclasses import dataclass
import dataclasses
from functools import wraps
import json
import threading
import time
import traceback
from typing import Any, Type
from flask import Flask, Response, jsonify, request
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

    if not os.path.exists(os.environ['BASE_PATH'] + '../frpc.toml'):
        subprocess.run(["mv", os.environ['BASE_PATH'] + 'bin/frp/frpc.toml', os.environ['BASE_PATH'] + '../frpc.toml'])

    if not os.path.exists(os.environ['BASE_PATH'] + '../frps.toml'):
        subprocess.run(["mv", os.environ['BASE_PATH'] + 'bin/frp/frps.toml', os.environ['BASE_PATH'] + '../frps.toml'])




def generate_client_config(server_token: str, server_address: str, proxies: str) -> str:
    """
    Generate a client configuration for frp.
    
    client_id: unique identifier for the client
    server_token: token for authentication with the server
    server_address: address of the frp server (ip:port)
    """
    
    config_string = f"""
serverAddr = "{server_address.split(':')[0]}"
serverPort = {server_address.split(':')[1]}

auth.method = "token"
auth.token = "{server_token}"
auth.additionalScopes = ["HeartBeats"]

"""
    
    config_string += proxies
    
    return config_string.strip()

def write_client_config(contents: str) -> None:
    """
    Write the client configuration to frpc.toml.
    
    contents: string containing the configuration
    """
    
    with open(os.environ['BASE_PATH'] + '../frpc.toml', 'w') as f:
        f.write(contents)





BASE = os.environ['BASE_PATH'] = os.path.abspath(__file__).removesuffix(os.path.basename(__file__))

@dataclass
class Config:
    type: str
    server_token: str

    # Only for server
    bind_port: int = None

    # Only for client
    client_id: str = None
    server_address: str = None
    master_port: int = None

    @staticmethod
    def verify_config(cfg: dict[str, Any]):
        """
        Verify the configuration loaded from config.toml.
        
        config params:
            type: client/server
            server-token: string (required for both client and server)
            client-id: string (required for client)
            server-address: ip:port (only for client, optional)
        """

        if 'type' not in cfg:
            raise ValueError('Missing "type" in config.toml')
        if cfg['type'] not in ['client', 'server']:
            raise ValueError('Invalid "type" in config.toml, must be "client" or "server"')
        
        if 'server-token' not in cfg:
            raise ValueError('Missing "server-token" in config.toml')
        
        if "master-port" not in cfg:
            raise ValueError('Missing "master-port" in config.toml')
        
        if cfg['type'] == 'client':
            if 'client-id' not in cfg:
                raise ValueError('Missing "client-id" in config.toml')

            if 'server-address' not in cfg:
                cfg['server-address'] = None
            else:
                try:
                    ip, port = cfg['server-address'].split(':')
                    cfg['server-address'] = f"{ip}:{int(port)}"
                except ValueError:
                    raise ValueError('Invalid "server-address" in config.toml, must be "ip:port"')
        else:
            
            if 'bind-port' not in cfg:
                raise ValueError('Missing "bind-port" in config.toml')


    @staticmethod
    def from_toml(config: dict[str, Any]) -> 'Config':
        Config.verify_config(config)
        return Config(
            type=config.get('type', 'client'),
            server_token=config.get('server-token', ''),
            client_id=config.get('client-id', None),
            server_address=config.get('server-address', None),
            master_port=config.get('master-port', None)
        )

CONFIG = Config.from_toml(toml.load(BASE + '../config.toml'))

try:
    install_latest_frp()
except Exception as e:
    # check if binaries exist already
    if not os.path.exists(BASE + 'bin/frp/frpc') or not os.path.exists(BASE + 'bin/frp/frps'):
        print(f"Failed to install frp: {e}")
        print("Please install frp manually or check your internet connection.")
        exit(1)


CLIENT = [f'{BASE}bin/frp/frpc', '-c', f'{BASE}../frpc.toml']
SERVER = [f'{BASE}bin/frp/frps', '-c', f'{BASE}../frps.toml']

stop_event    = threading.Event()
restart_event = threading.Event()

def check_server():
    while not stop_event.wait(60):
        try:
            addr = f"{CONFIG.server_address.split(':')[0]}:{CONFIG.master_port}"
            response = requests.get(f"http://{addr}/client/{CONFIG.client_id}/config?token={CONFIG.server_token}", timeout=5)
            if response.status_code != 200:
                print(f"Server returned status code {response.status_code}. Ignoring...")
                continue

            data = response.text.strip()

            write_client_config(
                generate_client_config(
                    server_token=CONFIG.server_token,
                    server_address=CONFIG.server_address,
                    proxies=data
                )
            )

            restart_event.set()

        except requests.RequestException as e:
            print(f"Failed to reach server: {e}. Restarting frp client...")
            traceback.print_exc()


def frp_monitor():
    """Keep an frp process alive and restart on request/failure."""
    while not stop_event.is_set():
        cmd = CLIENT if CONFIG.type == 'client' else SERVER
        try:
            with subprocess.Popen(cmd) as proc:
                # poll once a second so we can notice restart/stop requests
                while proc.poll() is None:
                    if stop_event.is_set() or restart_event.is_set():
                        proc.terminate()          # or .kill() if needed
                        proc.wait(timeout=10)
                        break
                    time.sleep(1)
        except Exception:
            print(traceback.format_exc())

        if stop_event.is_set():
            break
        restart_event.clear()
        print("Restarting in 5 seconds…")
        time.sleep(5)

threads = [
    threading.Thread(target=frp_monitor, daemon=True),
]

if CONFIG.type == 'client' and CONFIG.server_address:
    threads += [
        threading.Thread(target=check_server, daemon=True),
    ]

elif CONFIG.type == 'server':
    # parse existing server toml if exist
    data = {}
    if os.path.exists(BASE + '../frps.toml'):
        data = toml.load(BASE + '../frps.toml')

    # make sure above params are set
    data['bindPort'] = CONFIG.bind_port if CONFIG.bind_port else 7000
    data['auth'] = {}
    data['auth']['method'] = 'token'
    data['auth']['token'] = CONFIG.server_token
    data['auth']['additionalScopes'] = ['HeartBeats']

    # write back to frps.toml
    with open(BASE + '../frps.toml', 'w') as f:
        toml.dump(data, f)



app = Flask(__name__)

@dataclass
class Proxy:
    name: str
    type: str
    localIP: str
    localPort: int
    remotePort: int
    flags: list[str]

    def generate_config(self):
        config_string = f"""
[[proxies]]
name="{self.name}"
type="{self.type}"
localIP="{self.localIP}"
localPort={self.localPort}
remotePort={self.remotePort}
"""
        for flag in self.flags:
            config_string += f"{flag}\n"
        return config_string


@dataclass
class Client:
    id: str
    proxies: list[Proxy]

    def generate_config(self):
        res = ""
        for proxy in self.proxies:
            res += proxy.generate_config()

        return res
    


class DataclassJSONEncoder(json.JSONEncoder):
    """
    Recursively adds a __type__ key to all dataclass instances,
    including nested ones like proxies inside clients.
    """
    def default(self, obj: Any) -> Any:
        if dataclasses.is_dataclass(obj):
            return self._encode_dataclass(obj)
        return super().default(obj)

    def _encode_dataclass(self, obj: Any) -> dict:
        result = {"__type__": obj.__class__.__name__}
        for field in dataclasses.fields(obj):
            value = getattr(obj, field.name)
            result[field.name] = self._encode_value(value)
        return result

    def _encode_value(self, value: Any) -> Any:
        if dataclasses.is_dataclass(value):
            return self._encode_dataclass(value)
        elif isinstance(value, list):
            return [self._encode_value(v) for v in value]
        elif isinstance(value, dict):
            return {k: self._encode_value(v) for k, v in value.items()}
        else:
            return value


class DataclassJSONDecoder(json.JSONDecoder):
    """
    Recreates nested dataclasses automatically via object_hook.
    """
    _registry: dict[str, Type] = {
        "Client": Client,
        "Proxy":  Proxy,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self._hook, *args, **kwargs)

    def _hook(self, obj: dict) -> Any:
        cls_name = obj.pop("__type__", None)
        if cls_name is not None:
            cls = self._registry.get(cls_name)
            if cls is None:
                raise ValueError(f"Unknown dataclass type: {cls_name}")
            # The inner objects (if any) have already been processed
            return cls(**obj)
        return obj

config_file = f'{BASE}proxy_config.json'

def load_config() -> list[Client]:
    """
    Reads the JSON file and returns a list[Client].
    If the file is absent or empty → returns [].
    """
    if not os.path.exists(config_file):
        return []

    with open(config_file, "r") as f:
        data = json.load(f, cls=DataclassJSONDecoder)

    if isinstance(data, dict) and "clients" in data:
        return data["clients"]
    raise ValueError("Unexpected JSON structure in config file")

def save_config() -> None:
    """
    Serialises the list[Client] back to disk.
    """
    with open(config_file, "w") as f:
        json.dump({"clients": CONFIG_DB}, f, cls=DataclassJSONEncoder, indent=4)

CONFIG_DB: list[Client] = load_config()


def get_client(client_id):
    for client in CONFIG_DB:
        if client.id == client_id:
            return client
        
    raise ValueError("No such client id")


def auth_token(f):
    """
    Decorator to check if the request has a valid token.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.args.get("token")
        if not token or token != CONFIG.server_token:
            return jsonify({"error": "invalid token"}), 403
        return f(*args, **kwargs)
    return wrapper

@app.route("/clients", methods=["GET"])
@auth_token
def get_clients():
    """
    Get a list of all clients.
    """
    return Response(
        json.dumps(CONFIG_DB, cls=DataclassJSONEncoder),
        status=200,
        mimetype="application/json"
    )

@app.route("/client", methods=["PUT"])
@auth_token
def add_client():
    """
    Add a new client.
    Expects client id in the request body as JSON:
    {
        "id": "unique_client_id"
    }
    """
    data = request.json
    if not data or 'id' not in data:
        return jsonify({"error": "invalid request"}), 400

    client_id = data['id']
    if not client_id or any(client.id == client_id for client in CONFIG_DB):
        return jsonify({"error": "client already exists"}), 400

    new_client = Client(id=client_id, proxies=[])
    CONFIG_DB.append(new_client)
    save_config()

    return jsonify({"message": "client added successfully"}), 201

@app.route("/client/<client_id>", methods=["DELETE"])
@auth_token
def delete_client(client_id):
    """
    Delete a client by ID.
    """
    client = get_client(client_id)
    if client:
        CONFIG_DB.remove(client)
        save_config()
        return jsonify({"message": "client deleted successfully"}), 200

    return jsonify({"error": "invalid client_id"}), 400

@app.route("/client/<client_id>/config", methods=["GET"])
@auth_token
def client_config(client_id):
    """
    Get the configuration for a specific client.
    """
    try:
        client = get_client(client_id)
        return client.generate_config(), 200
    except ValueError:
        return jsonify({"error": "invalid client_id"}), 400

@app.route("/client/<client_id>/proxy", methods=["PUT"])
@auth_token
def add_proxy(client_id):
    """
    Add a new proxy to a client.
    Expects proxy details in the request body as JSON:
    {
        "name": "proxy_name",
        "type": "tcp/udp/http",
        "localIP": "<local_ip>",
        "localPort": <local_port>,
        "remotePort": <remote_port>
        "flags": ["flag1", "flag2"]
    }
    """
    data: dict = request.json
    if not data or not all(key in data for key in ['name', 'type', 'localIP', 'localPort', 'remotePort', 'flags']):
        return jsonify({"error": "invalid request"}), 400

    try:
        client = get_client(client_id)
    except ValueError:
        return jsonify({"error": "invalid client_id"}), 400
    
    if any(proxy.name == data['name'] for proxy in client.proxies):
        return jsonify({"error": "proxy with this name already exists"}), 400

    new_proxy = Proxy(
        name=data['name'],
        type=data['type'],
        localIP=data['localIP'],
        localPort=int(data['localPort']),
        remotePort=int(data['remotePort']),
        flags=data.get('flags', [])
    )

    client.proxies.append(new_proxy)
    save_config()

    return jsonify({"message": "proxy added successfully"}), 201

@app.route("/client/<client_id>/proxy/<proxy_name>", methods=["DELETE"])
@auth_token
def delete_proxy(client_id, proxy_name):
    """
    Delete a proxy from a client.
    """
    try:
        client = get_client(client_id)
    except ValueError:
        return jsonify({"error": "invalid client_id"}), 400

    proxy = next((p for p in client.proxies if p.name == proxy_name), None)
    if proxy:
        client.proxies.remove(proxy)
        save_config()
        return jsonify({"message": "proxy deleted successfully"}), 200

    return jsonify({"error": "proxy not found"}), 404

def run_api():
    """
    Start Flask in its own daemon thread so it doesn't block the main program.
    The built-in dev server is fine for an internal control plane; swap in
    Waitress or Gunicorn if you need real production robustness.
    """
    # For an internal service it's common to bind to 0.0.0.0 so LAN clients work
    app.run(host="0.0.0.0", port=CONFIG.master_port, threaded=True)










for t in threads: t.start()

try:
    while True:
        if CONFIG.type != "server":
            time.sleep(1)
            continue

        try:
            run_api()
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"Error occurred: {e}")

except KeyboardInterrupt:
    stop_event.set()
    for t in threads: t.join()
