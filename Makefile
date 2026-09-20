JAVA ?= $(or $(wildcard /opt/homebrew/opt/openjdk/bin/java),java)
GDK ?= $(HOME)/mars/m68k-elf
.DEFAULT_GOAL := all
.PHONY: all assets test clean
all: res/generated/object_patterns.bin
	$(MAKE) -f $(GDK)/makefile.gen JAVA=$(JAVA) LIBGCC="$(shell $(GDK)/bin/m68k-elf-gcc -m68000 -print-libgcc-file-name)"
	python3 tools/finalize_rom.py out/release/rom.bin
.venv/bin/python: requirements.txt
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt
res/generated/object_patterns.bin: tools/extract.py tools/arcade_source.py tools/extract_animation.py assets/board.json | .venv/bin/python
	.venv/bin/python tools/extract.py
assets: .venv/bin/python
	.venv/bin/python tools/extract.py
test: all
	.venv/bin/python tests/test_assets.py
	.venv/bin/python tests/test_runtime.py
	.venv/bin/python tests/test_animation.py
	.venv/bin/python tests/test_npc_runtime.py
clean:
	$(MAKE) -f $(GDK)/makefile.gen JAVA=$(JAVA) clean
