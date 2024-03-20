TARGETS:=
TARGETS+=lib/libsolfuzz_agave.so.1.17
TARGETS+=lib/libsolfuzz_agave.so.2.0
TARGETS+=lib/libsolfuzz_firedancer.so

.PHONY: all $(TARGETS)
all: $(TARGETS)

lib/libsolfuzz_agave.so.1.17:
	TERM=dumb $(MAKE) -C agave-v1.17 build RUST_VERSION=""
	ln -sf agave-v1.17/target/x86_64-unknown-linux-gnu/release/libsolfuzz_agave.so $@

lib/libsolfuzz_agave.so.2.0:
	TERM=dumb $(MAKE) -C agave-v2.0 build RUST_VERSION=""
	ln -sf agave-v2.0/target/x86_64-unknown-linux-gnu/release/libsolfuzz_agave.so $@

lib/libsolfuzz_firedancer.so:
	[ ! -f firedancer/opt/lib/libssl.a ] && firedancer/deps.sh fetch install || true
	$(MAKE) -C firedancer -j --output-sync=target CC=clang EXTRAS=fuzz build/native/clang/lib/libfd_exec_sol_compat.so
	ln -sf firedancer/build/native/clang/lib/libfd_exec_sol_compat.so $@

.PHONY: clean
clean:
	[ -d agave-v1.17 ] && $(MAKE) -C agave-v1.17 clean || true
	[ -d agave-v2.0 ] && $(MAKE) -C agave-v2.0 clean || true
	[ -d firedancer ] && rm -rf firedancer/opt && $(MAKE) -C firedancer distclean || true
