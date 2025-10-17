#!/usr/bin/env bash
set -euo pipefail

# Pin the Buf version you require
BUF_VERSION="${BUF_VERSION:-1.50.0}"

# Detect OS/arch
case "$(uname -s)" in
  Linux)  os="Linux" ;;
  Darwin) os="Darwin" ;;
  *) echo "Unsupported OS"; exit 1 ;;
esac
case "$(uname -m)" in
  x86_64|amd64) arch="x86_64" ;;
  arm64|aarch64) arch="arm64" ;;
  *) echo "Unsupported arch"; exit 1 ;;
esac

INSTALL_DIR="${HOME}/.local/bin"
BIN="${INSTALL_DIR}/buf"

need_install() {
  if [ ! -x "$BIN" ]; then return 0; fi
  current="$("$BIN" --version | awk '{print $NF}')"
  [ "$current" != "$BUF_VERSION" ]
}

if need_install; then
  mkdir -p "$INSTALL_DIR"
  url="https://github.com/bufbuild/buf/releases/download/v${BUF_VERSION}/buf-${os}-${arch}"
  tmp="$(mktemp -d)"
  echo "Installing Buf ${BUF_VERSION} from ${url}"
  curl -fsSL "$url" -o "${tmp}/buf"
  chmod +x "${tmp}/buf"
  mv "${tmp}/buf" "$BIN"
  rm -rf "$tmp"
fi

# Ensure ~/.local/bin on PATH
case ":$PATH:" in *":${INSTALL_DIR}:"*) ;; *) export PATH="${INSTALL_DIR}:${PATH}";; esac

buf --version
