import core
import toml
import os
import core.client
import core.server
import core.frp



os.environ['BASE_PATH'] = os.path.abspath(__file__).removesuffix(os.path.basename(__file__))

try:
    config = toml.load(os.environ['BASE_PATH'] + 'config.toml')
except FileNotFoundError:
    config = toml.load(os.environ['BASE_PATH'] + 'config.template.toml')

if config['type'] not in ['client', 'server']:
    raise ValueError('Invalid NTM type in config.toml')
os.environ['NTM_TYPE'] = config['type']
os.environ['NTM_HOST'] = config['serverHost']
os.environ['NTM_PORT'] = str(config['serverPort'])
os.environ['NTM_KEY'] = config['key']

core.frp.install_latest_frp()

if os.environ['NTM_TYPE'] == 'client':
    core.client.run()

elif os.environ['NTM_TYPE'] == 'server':
    core.server.run()