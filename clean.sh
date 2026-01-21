rm -rf test_suite_env || true
rm src/*.so || true
make -C impl clean
git submodule deinit --all -f
rm -rf protosol || true
rm -rf src/test_suite/flatbuffers || true
rm -rf src/test_suite/protos || true
deactivate || true
