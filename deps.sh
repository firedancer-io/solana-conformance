#!/usr/bin/env bash
#
# deps.sh - Build/install vendored dependencies for solana-conformance
#
# This script builds dependencies from vendored source in shlr/
# and downloads pre-built binaries (similar to solfuzz-agave's deps.sh)
#
# Usage:
#   ./deps.sh              # Install all dependencies
#   ./deps.sh flatc        # Build only flatc (from source)
#   ./deps.sh buf          # Download only buf
#   ./deps.sh --clean      # Remove built dependencies
#   ./deps.sh --status     # Show status of dependencies
#   ./deps.sh --help       # Show help
#
# Prerequisites (for building from source):
#   - cmake (for building flatbuffers)
#   - make
#   - C++ compiler (g++ or clang++)
#
# Dependencies installed:
#   - flatc: Built from shlr/flatbuffers submodule
#   - buf:   Downloaded pre-built binary
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Install prefix (matches solfuzz-agave convention)
PREFIX="$SCRIPT_DIR/opt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_step()  { echo -e "${BLUE}==>${NC} $*"; }

show_help() {
    cat << EOF
deps.sh - Build/install vendored dependencies for solana-conformance

Usage:
    ./deps.sh              Install all dependencies
    ./deps.sh flatc        Build only flatc (from shlr/flatbuffers source)
    ./deps.sh buf          Download only buf (pre-built binary)
    ./deps.sh --clean      Remove built dependencies (opt/ directory)
    ./deps.sh --status     Show status of dependencies
    ./deps.sh --help       Show this help message

Prerequisites (for flatc build):
    - cmake
    - make  
    - C++ compiler (g++ or clang++)

Dependencies:
    flatc - Built from shlr/flatbuffers submodule
    buf   - Downloaded pre-built binary

All binaries are installed to opt/bin/ for consistency.

Examples:
    ./deps.sh              # Install everything
    ./deps.sh --status     # Check what's installed
    ./deps.sh --clean      # Clean and rebuild
EOF
}

# Buf version
BUF_VERSION="${BUF_VERSION:-1.50.0}"

check_prerequisites() {
    local missing=()
    
    if ! command -v cmake &>/dev/null; then
        missing+=("cmake")
    fi
    
    if ! command -v make &>/dev/null; then
        missing+=("make")
    fi
    
    if ! command -v g++ &>/dev/null && ! command -v clang++ &>/dev/null; then
        missing+=("g++ or clang++")
    fi
    
    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing prerequisites: ${missing[*]}"
        echo ""
        echo "Install with:"
        echo "  RHEL/CentOS: sudo dnf install cmake make gcc-c++"
        echo "  Ubuntu:      sudo apt install cmake make g++"
        echo "  macOS:       brew install cmake"
        return 1
    fi
    
    return 0
}

check_submodules() {
    if [ ! -f "shlr/flatbuffers/CMakeLists.txt" ]; then
        log_warn "Submodules not initialized"
        log_info "Initializing git submodules..."
        git submodule update --init --recursive
        
        if [ ! -f "shlr/flatbuffers/CMakeLists.txt" ]; then
            log_error "Failed to initialize submodules"
            echo ""
            echo "Try manually:"
            echo "  git submodule update --init --recursive"
            return 1
        fi
    fi
    return 0
}

install_flatbuffers() {
    log_step "Building flatbuffers (flatc only)"
    
    check_submodules || return 1
    
    local build_dir="$PREFIX/build/flatbuffers"
    mkdir -p "$build_dir"
    
    log_info "Configuring flatbuffers..."
    cmake \
        -S shlr/flatbuffers \
        -B "$build_dir" \
        -G "Unix Makefiles" \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX:PATH="$PREFIX" \
        -DFLATBUFFERS_BUILD_TESTS=OFF \
        -DFLATBUFFERS_BUILD_FLATC=ON \
        -DFLATBUFFERS_BUILD_FLATLIB=OFF \
        -DFLATBUFFERS_BUILD_FLATHASH=OFF
    
    log_info "Building flatc..."
    make -C "$build_dir" flatc -j "$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)"
    
    log_info "Installing flatc..."
    cmake --install "$build_dir" --config Release
    
    # Verify
    if [ -x "$PREFIX/bin/flatc" ]; then
        log_info "Successfully built flatc"
        "$PREFIX/bin/flatc" --version
    else
        log_error "Build failed - flatc not found"
        return 1
    fi
}

install_buf() {
    log_step "Installing buf v${BUF_VERSION}"
    
    # Detect OS/arch
    local os arch
    case "$(uname -s)" in
        Linux)  os="Linux" ;;
        Darwin) os="Darwin" ;;
        *)
            log_error "Unsupported OS: $(uname -s)"
            return 1
            ;;
    esac
    
    case "$(uname -m)" in
        x86_64|amd64) arch="x86_64" ;;
        arm64|aarch64) arch="arm64" ;;
        *)
            log_error "Unsupported architecture: $(uname -m)"
            return 1
            ;;
    esac
    
    local url="https://github.com/bufbuild/buf/releases/download/v${BUF_VERSION}/buf-${os}-${arch}"
    local target="$PREFIX/bin/buf"
    
    mkdir -p "$PREFIX/bin"
    
    # Check if already installed with correct version
    if [ -x "$target" ]; then
        local current_version
        current_version="$("$target" --version 2>/dev/null | awk '{print $NF}' || echo "")"
        if [ "$current_version" = "$BUF_VERSION" ]; then
            log_info "buf v${BUF_VERSION} already installed"
            return 0
        fi
        log_info "Upgrading buf from v${current_version} to v${BUF_VERSION}"
    fi
    
    log_info "Downloading buf from: $url"
    
    local tmp
    tmp="$(mktemp -d)"
    if curl -fsSL "$url" -o "${tmp}/buf"; then
        chmod +x "${tmp}/buf"
        mv "${tmp}/buf" "$target"
        rm -rf "$tmp"
        
        if [ -x "$target" ]; then
            log_info "Successfully installed buf"
            "$target" --version
        else
            log_error "Installation failed - buf not executable"
            return 1
        fi
    else
        rm -rf "$tmp"
        log_error "Failed to download buf from: $url"
        echo ""
        echo "    Check your network connection or try:"
        echo "      curl -fsSL '$url' -o opt/bin/buf && chmod +x opt/bin/buf"
        return 1
    fi
}

show_status() {
    echo "=== Dependency Status ==="
    echo ""
    echo "Install prefix: $PREFIX"
    echo "Source directory: shlr/"
    echo ""
    
    # Check submodules
    if [ -f "shlr/flatbuffers/CMakeLists.txt" ]; then
        local fb_version
        fb_version=$(cd shlr/flatbuffers && git describe --tags 2>/dev/null || echo "unknown")
        echo -e "flatbuffers source: ${GREEN}present${NC} ($fb_version)"
    else
        echo -e "flatbuffers source: ${RED}missing${NC} (run: git submodule update --init)"
    fi
    
    # Check flatc
    if [ -x "$PREFIX/bin/flatc" ]; then
        echo -e "flatc: ${GREEN}installed${NC}"
        echo "  Path: $PREFIX/bin/flatc"
        echo "  Version: $("$PREFIX/bin/flatc" --version 2>/dev/null || echo 'unknown')"
    else
        echo -e "flatc: ${RED}not installed${NC}"
    fi
    
    # Check buf
    if [ -x "$PREFIX/bin/buf" ]; then
        local buf_ver
        buf_ver="$("$PREFIX/bin/buf" --version 2>/dev/null | awk '{print $NF}' || echo 'unknown')"
        echo -e "buf: ${GREEN}installed${NC}"
        echo "  Path: $PREFIX/bin/buf"
        echo "  Version: $buf_ver"
        if [ -d "$PREFIX/cache/buf" ]; then
            echo "  Cache: $PREFIX/cache/buf"
        fi
    else
        echo -e "buf: ${RED}not installed${NC}"
    fi
    
    # Check protosol submodule
    if [ -d "$SCRIPT_DIR/shlr/protosol/proto" ]; then
        local proto_ver
        proto_ver="$(cd "$SCRIPT_DIR/shlr/protosol" && git describe --tags 2>/dev/null || echo 'unknown')"
        echo -e "protosol: ${GREEN}present${NC} ($proto_ver)"
        echo "  Path: shlr/protosol"
    else
        echo -e "protosol: ${RED}missing${NC} (run: git submodule update --init)"
    fi
    
    echo ""
    echo "Run './deps.sh' to install missing dependencies"
}

clean_deps() {
    log_step "Cleaning built dependencies..."
    
    if [ -d "$PREFIX" ]; then
        log_info "Removing $PREFIX"
        rm -rf "$PREFIX"
        log_info "Done"
    else
        log_info "Nothing to clean (opt/ doesn't exist)"
    fi
}

install_all() {
    log_step "Installing all dependencies for solana-conformance"
    echo ""
    echo "Install prefix: $PREFIX"
    echo "Source: shlr/flatbuffers (built), buf (downloaded)"
    echo ""
    
    mkdir -p "$PREFIX/bin"
    
    # Install buf first (no build dependencies required)
    install_buf || log_warn "buf installation failed (continuing...)"
    
    echo ""
    
    # Build flatc (requires cmake, make, g++)
    check_prerequisites || {
        log_warn "Missing build prerequisites - skipping flatc"
        echo "    Install cmake, make, g++ to build flatc from source"
        echo ""
        show_status
        return 1
    }
    
    install_flatbuffers
    
    echo ""
    log_info "All dependencies installed!"
    echo ""
    echo "Binaries available at: $PREFIX/bin/"
    echo "  - flatc: $PREFIX/bin/flatc"
    echo "  - buf:   $PREFIX/bin/buf"
}

# Main
case "${1:-}" in
    --help|-h)
        show_help
        ;;
    --clean)
        clean_deps
        ;;
    --status)
        show_status
        ;;
    flatc)
        check_prerequisites || exit 1
        mkdir -p "$PREFIX/bin"
        install_flatbuffers
        ;;
    buf)
        mkdir -p "$PREFIX/bin"
        install_buf
        ;;
    "")
        install_all
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Run './deps.sh --help' for usage"
        exit 1
        ;;
esac
