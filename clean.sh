rm -rf test_suite_env || true
rm src/test_suite/invoke_pb2.py || true
rm src/*.so || true
make -C impl clean
git submodule deinit --all -f
deactivate || true
