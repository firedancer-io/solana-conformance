rm -rf test_suite_env || true
rm src/*.so || true
make -C impl clean
git submodule deinit --all -f
rm -rf protosol || true
deactivate || true
