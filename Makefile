# BugfixedHL x Opposing Force - Speedrun Merge Kit
PYTHON ?= python3
CXX    ?= g++
ROOT   := $(CURDIR)

.PHONY: help verify hygiene tidy test test-py test-cpp test-op4 test-op4-fixups gen route-check merge merge-offline bhl-plan bhl-base verify-bhl-base fetch serve build build-cmake verify-sdk package build-dlls build-dlls-check build-dlls-zig noexcept-check mod clean

help:
	@echo "verify        - hygiene + python tests + C++ checks + generation + merge + package"
	@echo "hygiene       - check whitespace, JSON, imports, docs links, fixtures"
	@echo "tidy          - remove __pycache__/stale stage dirs, then run hygiene"
	@echo "fetch         - download pinned, checksum-verified upstream SDKs"
	@echo "merge         - merge real upstreams into build/merged-real"
	@echo "bhl-plan      - (legacy) list the OP4-base bhl-systems-1 shims"
	@echo "bhl-base      - rebuild bhl-op4/ = BHL tree + merged OP4 systems/weapons"
	@echo "verify-bhl-base - verify provenance + CMake-wired OP4 sources compile"
	@echo "merge-offline - merge bundled fixtures (no network) into build/merged"
	@echo "gen           - regenerate C++ route header from data/op4_route.json"
	@echo "serve         - run the live dashboard on 0.0.0.0:8000"
	@echo "build         - build the speedrun core + C++ tests (g++, no deps)"
	@echo "test-op4      - executable tests of the real OP4 algorithms in the DLLs"
	@echo "test-op4-fixups - executable tests of the extracted real OP4 fixup bodies"
	@echo "build-cmake   - same via CMake (optional)"
	@echo "verify-sdk    - syntax-check injected files against the real SDK headers"
	@echo "package       - build dist/bhl-op4-speedrun-overlay.zip + MANIFEST.json"
	@echo "build-dlls    - build 32-bit client.so + hl.so from build/merged-real"
	@echo "build-dlls-check - preflight only (toolchain / vgui.so / patched makefiles)"
	@echo "build-dlls-zig - build ELF32 client.so/hl.so with Zig, no gcc-multilib/vgui.so needed"
	@echo "mod           - create the standalone bhlop4/ mod folder + zip (never gearbox/)"
	@echo "clean         - remove build/, dist/ and fetched SDK cache"

verify: hygiene test-py gen route-check noexcept-check test-cpp test-op4 test-op4-fixups verify-bhl-base merge-offline package mod
	@echo "== ALL CHECKS PASSED =="

test: test-py test-cpp

hygiene:
	$(PYTHON) tools/check_hygiene.py

tidy:
	find . -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/.stage-* build/.old-*
	$(PYTHON) tools/check_hygiene.py

test-py:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

test-cpp: build
	./build/speedrun_test

test-op4:
	mkdir -p build
	$(CXX) -std=c++17 -O1 -Wall -Wextra -Wpedantic tests/cpp/test_op4_algorithms.cpp -o build/op4_algorithm_test
	./build/op4_algorithm_test

test-op4-fixups:
	mkdir -p build
	$(PYTHON) tools/gen_op4_fixup_harness.py
	$(CXX) -std=c++17 -O1 -Wall -Wextra -Wpedantic build/op4_fixup_harness.cpp -o build/op4_fixup_harness
	./build/op4_fixup_harness

build:
	mkdir -p build
	$(CXX) -std=c++17 -O2 -Wall -Wextra -Wpedantic -Isrc/speedrun \
		src/speedrun/sr_core.cpp tests/cpp/test_speedrun.cpp -o build/speedrun_test

build-cmake:
	cmake -S . -B build/cmake -DCMAKE_BUILD_TYPE=Release
	cmake --build build/cmake -j 2

verify-sdk:
	$(PYTHON) tools/verify_sdk.py --tree build/merged-real

build-dlls:
	$(PYTHON) tools/build_dlls.py

build-dlls-check:
	$(PYTHON) tools/build_dlls.py --check --require-tree

build-dlls-zig:
	$(PYTHON) tools/build_dlls_zig.py

noexcept-check:
	$(CXX) -std=c++17 -fno-exceptions -Isrc/speedrun -fsyntax-only src/speedrun/sr_core.cpp

mod:
	$(PYTHON) tools/create_mod.py

package:
	$(PYTHON) tools/package_mod.py

gen:
	$(PYTHON) tools/gen_route_header.py --check

route-check:
	$(PYTHON) -m merge.cli route --check

merge-offline:
	$(PYTHON) -m merge.cli run --offline
	$(PYTHON) -m merge.bhl --tree build/merged

merge:
	$(PYTHON) -m merge.cli run --out build/merged-real
	$(PYTHON) -m merge.bhl --tree build/merged-real

bhl-plan:
	$(PYTHON) -m merge.bhl --plan

bhl-base:
	$(PYTHON) -m merge.bhl_base --out bhl-op4

verify-bhl-base:
	$(PYTHON) -m merge.bhl_base --check --out bhl-op4
	$(PYTHON) tools/verify_bhl_base.py --check

fetch:
	$(PYTHON) -m merge.cli fetch

serve:
	$(PYTHON) web/app.py

clean:
	rm -rf build dist .cache/upstreams
