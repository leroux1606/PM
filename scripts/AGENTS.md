# Scripts

Start and stop the **local Podman Compose** stack from the **repository root** (uses **`compose.yaml`**).

| Script | OS |
|--------|-----|
| `start.sh` | macOS / Linux |
| `stop.sh` | macOS / Linux |
| `start.ps1` | Windows (PowerShell) |
| `stop.ps1` | Windows (PowerShell) |

On Unix, if needed: `chmod +x start.sh stop.sh`.

The start scripts ensure **`.env`** exists by copying **`.env.example`** when missing. See **`docs/DEV_CONTAINER.md`**.
