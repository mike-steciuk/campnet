# Development and router access

## Local environment

CampNet targets Python 3.11 or newer. From PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pytest
ruff check .
mypy campnet tests
```

## Router SSH authentication

Use a dedicated SSH key for CampNet. Never place the router's root password,
a private key, or a bearer token in this repository, a survey, a command-line
argument, or a chat message.

Generate the key on the computer that will run CampNet:

```powershell
ssh-keygen -t ed25519 -f "$env:USERPROFILE\.ssh\campnet_router" -C "campnet-router"
```

Protect the private key with a passphrase and load it into Windows `ssh-agent`.
Only the `.pub` file may be copied or shared. On OpenWrt/Dropbear, append that
public key to `/etc/dropbear/authorized_keys`, either through the router UI or
during one initial password-authenticated SSH session.

Add a local SSH configuration entry outside this repository:

```text
Host campnet-router
    HostName 192.168.8.1
    User root
    IdentityFile ~/.ssh/campnet_router
    IdentitiesOnly yes
```

Verify key-only access before changing password-authentication settings:

```powershell
ssh -o PasswordAuthentication=no campnet-router true
```

Do not disable password authentication until key authentication is confirmed
and another router recovery method is available. CampNet will invoke the local
SSH client and rely on its agent/configuration rather than handle credentials.
