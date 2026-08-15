# Development and router access

## Local environment

CampNet targets Python 3.11 or newer. From PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pytest
ruff check .
mypy campnet tests
```

Install the optional speed-test adapter with:

```powershell
python -m pip install -e ".[speedtest]"
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
## Adding an AT command

1. Add the definition to `campnet.at_registry` with a stable identifier and a
   reviewed safety classification.
2. Add sanitized recorded responses under `tests/fixtures` and connect a
   parser where applicable.
3. Reference the identifier from runtime code; do not copy the command into a
   second command list.
4. Add validation records per modem, firmware, router, and transport. Keep
   documented behavior, observations, interpretation, and open questions
   separate.
5. Run `python -m campnet.at_docs`, then tests, Ruff, and strict mypy.

Examples in documentation must put useful comments immediately before the
shell or AT command. Never commit raw validation data until identifiers,
coordinates, credentials, and message content have been redacted.
