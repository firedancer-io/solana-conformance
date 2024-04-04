git submodule init && git submodule update
sudo dnf install -y gcc-toolset-12 || true
source /opt/rh/gcc-toolset-12/enable
python3.11 -m venv test_suite_env
source test_suite_env/bin/activate
make -j -C impl
pip install .
protoc --python_out=src/test_suite invoke.proto
