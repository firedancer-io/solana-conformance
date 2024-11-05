TARGETS:=
TARGETS+=lib/libsolfuzz_agave_v1.17.so
TARGETS+=lib/libsolfuzz_agave_v2.0.so
TARGETS+=lib/libsolfuzz_agave_v2.1.0.so
TARGETS+=lib/libsolfuzz_firedancer.so

.PHONY: all $(TARGETS)
all: $(TARGETS)

lib/libsolfuzz_agave_v1.17.so:
	mkdir -p lib
	TERM=dumb $(MAKE) -C agave-v1.17 build RUST_VERSION=""
	ln -sf ../agave-v1.17/target/x86_64-unknown-linux-gnu/release/libsolfuzz_agave.so lib/libsolfuzz_agave_sancov_v1.17.so
	TERM=dumb cd agave-v1.17 && cargo build --lib
	ln -sf ../agave-v1.17/target/debug/libsolfuzz_agave.so lib/libsolfuzz_agave_v1.17.so

lib/libsolfuzz_agave_v2.0.so:
	mkdir -p lib
	TERM=dumb $(MAKE) -C agave-v2.0 build RUST_VERSION=""
	ln -sf ../agave-v2.0/target/x86_64-unknown-linux-gnu/release/libsolfuzz_agave.so lib/libsolfuzz_agave_sancov_v2.0.so
	TERM=dumb cd agave-v2.0 && cargo build --lib
	ln -sf ../agave-v2.0/target/debug/libsolfuzz_agave.so lib/libsolfuzz_agave_v2.0.so

lib/libsolfuzz_agave_v2.1.0.so:
	mkdir -p lib
	TERM=dumb $(MAKE) -C agave-v2.1.0 build RUST_VERSION=""
	ln -sf ../agave-v2.1.0/target/x86_64-unknown-linux-gnu/release/libsolfuzz_agave.so lib/libsolfuzz_agave_sancov_v2.1.0.so
	TERM=dumb cd agave-v2.1.0 && cargo build --lib
	ln -sf ../agave-v2.1.0/target/debug/libsolfuzz_agave.so lib/libsolfuzz_agave_v2.1.0.so

lib/libsolfuzz_firedancer.so:
	mkdir -p lib
	[ ! -f firedancer/opt/lib/libssl.a ] && firedancer/deps.sh +dev fetch install || true
	$(MAKE) -C firedancer -j --output-sync=target CC=clang EXTRAS=fuzz BUILDDIR=sancov build/sancov/lib/libfd_exec_sol_compat.so
	ln -sf ../firedancer/build/sancov/lib/libfd_exec_sol_compat.so lib/libsolfuzz_firedancer_sancov.so
	$(MAKE) -C firedancer -j --output-sync=target CC=clang build/native/clang/lib/libfd_exec_sol_compat.so
	ln -sf ../firedancer/build/native/clang/lib/libfd_exec_sol_compat.so lib/libsolfuzz_firedancer.so
	ln -sf ../firedancer/build/native/clang/lib/libfd_ballet.a lib/libfd_ballet.a

solfuzz/build/fuzz_sol_prog:
	mkdir -p bin
	[ ! -f solfuzz/shlr/protobuf ] && cd solfuzz && git submodule update --init --recursive && cd - || true
	[ ! -f solfuzz/opt/bin/protoc ] && cd solfuzz && sys/deps.sh && cd - || true
	cd solfuzz && cmake -B build -DCMAKE_CXX_COMPILER=clang++ . && cmake --build build && cd -

bin/fuzz_sol_prog: solfuzz/build/fuzz_sol_prog
	mkdir -p bin
	ln -sf $(shell realpath $<) $@

.PHONY: clean
clean:
	find lib -name '*.so' -delete || true
	find lib -name '*.a' -delete || true
	find bin -type l -delete || true
	[ -d agave-v1.17 ] && $(MAKE) -C agave-v1.17 clean || true
	[ -d agave-v2.0 ] && $(MAKE) -C agave-v2.0 clean || true
	[ -d agave-v2.1.0 ] && $(MAKE) -C agave-v2.1.0 clean || true
	[ -d firedancer ] && rm -rf firedancer/opt && $(MAKE) -C firedancer distclean || true
	[ -d solfuzz/build ] && rm -rf solfuzz/build || true
