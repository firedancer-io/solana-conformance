git submodule init && git submodule update
sudo dnf install -y gcc-toolset-12 || true
source /opt/rh/gcc-toolset-12/enable
python3.11 -m venv test_suite_env
source test_suite_env/bin/activate
sudo dnf install -y python3.11-devel || true
make -j -C impl
pip install -e ".[dev]"
