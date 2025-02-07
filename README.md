# NTM - NAT Tunnel Manager

NTM is a simple manager for [fatedier/frp](https://github.com/fatedier/frp), providing a quick way to install, configure, and run FRP (Fast Reverse Proxy) as a systemd service on Linux. NTM automatically downloads the latest FRP release from GitHub and runs either the client (frpc) or server (frps) mode based on your configuration.

## Features

- **Easy Installation**: One-line script to set up NTM and all dependencies.  
- **Auto-Updates**: Automatically fetches and updates FRP to the latest release.  
- **Systemd Service**: Installs a persistent service for FRP that restarts on failures.  
- **Quick Configuration**: Provides a helper script (`ntm-config`) to edit FRP’s config and automatically restart the service if changes are detected.  
- **Uninstallation**: Simple script to cleanly remove all traces of NTM from your system.

## Getting Started

### 1. Clone This Repository

```bash
git clone https://github.com/yniverz/ntm.git
cd ntm
```

### 2. Install NTM

```bash
sudo ./install.sh
```

- This script will:
  - Install Python 3, pip, and virtualenv if not already installed.
  - Copy files to `/opt/ntm` (by default).
  - Create a systemd service at `/etc/systemd/system/ntm.service`.
  - Create a dedicated Python virtual environment and install dependencies.
  - Start and enable the `ntm` service so it runs at boot.

### 3. Configure NTM

By default, NTM uses a template that sets it up in **client** mode (`type="client"` in `config.toml`).  
You can switch it to **server** mode by editing the config.

Use the helper script `ntm-config`:

- **Edit NTM config**:
  ```bash
  ntm-config
  ```

- **Edit frp client config (frpc)**:
  ```bash
  ntm-config -c
  ```
- **Edit frp server config (frps)**:
  ```bash
  ntm-config -s
  ```

If you edit the config, NTM will detect changes and automatically restart the service.

### 4. Viewing Logs

Service logs are written to `/var/log/ntm.log`. Check them using:

```bash
tail -f /var/log/ntm.log
```

### 5. Updating NTM

If you’ve pulled new changes from the repo or want to upgrade dependencies, run:

```bash
sudo ./update.sh
```

This will:
- Stop the `ntm` service.
- Copy updated `core` files to `/opt/ntm`.
- Update Python dependencies in the virtual environment.
- Restart the `ntm` service.

### 6. Uninstalling NTM

To completely remove NTM from your system:

```bash
sudo ./uninstall.sh
```

This will:
- Stop and disable the systemd service.
- Remove `/opt/ntm`, the systemd unit file, and the log file.
- Remove the `ntm-config` command from `/usr/local/bin`.
