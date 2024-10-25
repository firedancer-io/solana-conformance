# Install the toolkit on Ubuntu.

# Clone repositories.
cd impl
git clone http://github.com/firedancer-io/firedancer.git
git clone -b agave-v1.17 http://github.com/firedancer-io/solfuzz-agave.git agave-v1.17
git clone -b agave-v2.0 http://github.com/firedancer-io/solfuzz-agave.git agave-v2.0
cd ..

# Configure GCC.
sudo apt install -y build-essential software-properties-common
sudo add-apt-repository -y ppa:ubuntu-toolchain-r/test
sudo apt update
sudo apt install -y gcc-12 g++-12
sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-12 20
sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-12 20

# Configure Python virtual environment.
sudo apt install -y python3.11 python3.11-dev
python3.11 -m venv test_suite_env
source test_suite_env/bin/activate

# Bootstrap environment.
make -j -C impl
pip install -e ".[dev]"
pre-commit install
