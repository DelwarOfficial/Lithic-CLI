# Platform-Specific Guidelines

## 🍏 Mac Users

### Installation

```bash
# Install from source
git clone https://github.com/DelwarOfficial/Lithic-CLI.git
cd Lithic-CLI
uv sync

# pip install lithic-cli and brew install lithic-cli are planned
```

### Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Open terminal | `Cmd + Space` → type "Terminal" |
| Clear screen | `Cmd + K` |
| Cancel running command | `Ctrl + C` |
| Path autocomplete | `Tab` key |
| Command history | `↑` / `↓` arrow keys |

### Common Issues & Fixes

- **Python version**: Ensure Python 3.12+ is installed (`python3 --version`)
- **Permission denied**: Use `sudo` with caution, or install with `--user` flag
- **Virtual environment**: Recommended to avoid dependency conflicts

```bash
git clone https://github.com/DelwarOfficial/Lithic-CLI.git
cd Lithic-CLI
uv sync
```

---

## 🪟 Windows Users

### Installation

```powershell
# Install from source
git clone https://github.com/DelwarOfficial/Lithic-CLI.git
cd Lithic-CLI
uv sync
```

### Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Open terminal | `Win + R` → type "cmd" or "powershell" |
| Clear screen | `cls` (CMD) or `Clear-Host` (PowerShell) |
| Cancel running command | `Ctrl + C` |
| Path autocomplete | `Tab` key |
| Command history | `↑` / `↓` arrow keys |

### Common Issues & Fixes

- **Python path**: Ensure Python is in your PATH environment variable
- **Long paths**: Enable long path support in Windows (registry or group policy)
- **Virtual environment**: Use PowerShell for best experience

```powershell
git clone https://github.com/DelwarOfficial/Lithic-CLI.git
cd Lithic-CLI
uv sync
```

---

## 🔧 Universal Guidelines

### Pre-Installation Checklist

- [ ] Python 3.12+ installed
- [ ] `uv` is installed (`pip install uv` or `winget install astral.uv`)
- [ ] Internet connection for first-time install

### Troubleshooting

1. **Command not found**: Check if Python scripts directory is in PATH
2. **Permission errors**: Install with `--user` flag or use virtual environment
3. **Graph generation fails**: Ensure working directory has read/write access

### Resources

- [Official Documentation](docs/architecture.md)
- [GitHub Issues](https://github.com/DelwarOfficial/Lithic-CLI/issues)
--

**Need help?** Provide your OS version and the exact error message for faster support.
