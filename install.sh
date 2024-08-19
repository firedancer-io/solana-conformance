cd impl
git clone http://github.com/firedancer-io/firedancer.git
git clone -b agave-v1.17 http://github.com/firedancer-io/solfuzz-agave.git agave-v1.17
git clone -b agave-v2.0 http://github.com/firedancer-io/solfuzz-agave.git agave-v2.0
cd ..
sudo dnf install -y gcc-toolset-12 || true
source /opt/rh/gcc-toolset-12/enable
python3.11 -m venv test_suite_env
source test_suite_env/bin/activate
sudo dnf install -y python3.11-devel || true
make -j -C impl
pip install -e ".[dev]"
pre-commit install
