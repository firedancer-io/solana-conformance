TARGETS:=
TARGETS+=lib/libsolfuzz_agave_v1.17.so
TARGETS+=lib/libsolfuzz_agave_v2.0.so
TARGETS+=lib/libsolfuzz_firedancer.so

.PHONY: all $(TARGETS)
all: $(TARGETS)

lib/libsolfuzz_agave_v1.17.so:
	mkdir -p lib
	TERM=dumb $(MAKE) -C agave-v1.17 build RUST_VERSION=""
	ln -sf ../agave-v1.17/target/x86_64-unknown-linux-gnu/release/libsolfuzz_agave.so lib/libsolfuzz_agave_sancov_v1.17.so
	TERM=dumb cd agave-v1.17 && cargo build --release --lib
	ln -sf ../agave-v1.17/target/release/libsolfuzz_agave.so lib/libsolfuzz_agave_v1.17.so

lib/libsolfuzz_agave_v2.0.so:
	mkdir -p lib
	TERM=dumb $(MAKE) -C agave-v2.0 build RUST_VERSION=""
	ln -sf ../agave-v2.0/target/x86_64-unknown-linux-gnu/release/libsolfuzz_agave.so lib/libsolfuzz_agave_sancov_v2.0.so
	TERM=dumb cd agave-v2.0 && cargo build --release --lib
	ln -sf ../agave-v2.0/target/release/libsolfuzz_agave.so lib/libsolfuzz_agave_v2.0.so

lib/libsolfuzz_firedancer.so:
	mkdir -p lib
	[ ! -f firedancer/opt/lib/libssl.a ] && firedancer/deps.sh fetch install || true
	$(MAKE) -C firedancer -j --output-sync=target CC=clang EXTRAS=fuzz BUILDDIR=sancov build/sancov/lib/libfd_exec_sol_compat.so
	ln -sf ../firedancer/build/sancov/lib/libfd_exec_sol_compat.so lib/libsolfuzz_firedancer_sancov.so
	$(MAKE) -C firedancer -j --output-sync=target CC=clang build/native/clang/lib/libfd_exec_sol_compat.so
	ln -sf ../firedancer/build/native/clang/lib/libfd_exec_sol_compat.so lib/libsolfuzz_firedancer.so
	ln -sf ../firedancer/build/native/clang/lib/libfd_ballet.a lib/libfd_ballet.a

.PHONY: clean
clean:
	find lib -name '*.so' -delete || true
	[ -d agave-v1.17 ] && $(MAKE) -C agave-v1.17 clean || true
	[ -d agave-v2.0 ] && $(MAKE) -C agave-v2.0 clean || true
	[ -d firedancer ] && rm -rf firedancer/opt && $(MAKE) -C firedancer distclean || true
