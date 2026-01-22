#!/usr/bin/env bash
set -euo pipefail

# Find or install the FlatBuffers compiler (flatc)
#
# This script checks for flatc in the following locations:
# 1. System PATH
# 2. solfuzz build directory (if SOLFUZZ_DIR is set or auto-detected)
# 3. Download and install if not found

FLATC_VERSION="${FLATC_VERSION:-24.3.25}"
INSTALL_DIR="${HOME}/.local/bin"

# Try to find flatc in various locations
find_flatc() {
    # Check PATH first
    if command -v flatc &>/dev/null; then
        command -v flatc
        return 0
    fi
    
    # Check solfuzz directory (auto-detect or from env)
    local script_parent
    if [ -n "${BASH_SOURCE[0]:-}" ]; then
        script_parent="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)" || true
    fi
    
    local solfuzz_dirs=(
        "${SOLFUZZ_DIR:-}"
        "/data/$USER/solfuzz"
        "/data/$USER/repos/solfuzz"
        "$HOME/solfuzz"
        "../solfuzz"
        "${script_parent:-}/solfuzz"
    )
    
    for dir in "${solfuzz_dirs[@]}"; do
        if [ -n "$dir" ] && [ -x "$dir/bin/flatc" ]; then
            echo "$dir/bin/flatc"
            return 0
        fi
        if [ -n "$dir" ] && [ -x "$dir/opt/build/flatbuffers/flatc" ]; then
            echo "$dir/opt/build/flatbuffers/flatc"
            return 0
        fi
    done
    
    # Check local install
    if [ -x "$INSTALL_DIR/flatc" ]; then
        echo "$INSTALL_DIR/flatc"
        return 0
    fi
    
    return 1
}

# Try to find existing flatc
if FLATC_PATH=$(find_flatc); then
    echo "Found flatc at: $FLATC_PATH"
    "$FLATC_PATH" --version
    export FLATC_PATH
    exit 0
fi

# Need to install - try to download
echo "flatc not found, attempting to install FlatBuffers ${FLATC_VERSION}..."

# Detect OS/arch
case "$(uname -s)" in
    Linux)  os="Linux" ;;
    Darwin) os="Mac" ;;
    *) echo "Unsupported OS"; exit 1 ;;
esac

case "$(uname -m)" in
    x86_64|amd64) arch="x86_64" ;;
    arm64|aarch64) arch="arm64" ;;
    *) echo "Unsupported arch"; exit 1 ;;
esac

mkdir -p "$INSTALL_DIR"
tmp="$(mktemp -d)"

# Try different URL formats (GitHub release naming varies by version)
urls=(
    "https://github.com/google/flatbuffers/releases/download/v${FLATC_VERSION}/${os}.flatc.binary.g++-13.zip"
    "https://github.com/google/flatbuffers/releases/download/v${FLATC_VERSION}/${os}.flatc.binary.clang++-15.zip"
    "https://github.com/google/flatbuffers/releases/download/v${FLATC_VERSION}/${os}.flatc.binary.zip"
    "https://github.com/google/flatbuffers/releases/download/v${FLATC_VERSION}/flatc_${os}.zip"
    "https://github.com/google/flatbuffers/releases/download/v${FLATC_VERSION}/${os}_flatc_binary.zip"
)

downloaded=false
for url in "${urls[@]}"; do
    echo "Trying: $url"
    if curl -fsSL "$url" -o "${tmp}/flatc.zip" 2>/dev/null; then
        downloaded=true
        break
    fi
done

if [ "$downloaded" = false ]; then
    echo ""
    echo "ERROR: Failed to download flatc."
    echo ""
    echo "Please provide flatc via one of:"
    echo "  1. Set SOLFUZZ_DIR to point to solfuzz with built flatc"
    echo "  2. Install flatc to PATH"
    echo "  3. Build from source: https://github.com/google/flatbuffers"
    echo ""
    echo "The solfuzz repository includes flatc at: \$SOLFUZZ_DIR/bin/flatc"
    rm -rf "$tmp"
    exit 1
fi

cd "$tmp"
unzip -q flatc.zip
if [ -f flatc ]; then
    chmod +x flatc
    mv flatc "$INSTALL_DIR/flatc"
else
    # Some archives have flatc in a subdirectory
    find . -name "flatc" -type f -exec chmod +x {} \; -exec mv {} "$INSTALL_DIR/flatc" \;
fi
cd - >/dev/null
rm -rf "$tmp"

FLATC_PATH="$INSTALL_DIR/flatc"
echo "Installed flatc to: $FLATC_PATH"
"$FLATC_PATH" --version

# Ensure ~/.local/bin on PATH
case ":$PATH:" in *":${INSTALL_DIR}:"*) ;; *) export PATH="${INSTALL_DIR}:${PATH}";; esac

# Export for other scripts
export FLATC_PATH
