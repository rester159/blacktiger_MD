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
res/generated/object_patterns.bin: tools/extract.py tools/arcade_source.py tools/extract_animation.py tools/actor_contract.py tools/extract_hidden.py tools/extract_skeleton.py tools/extract_loot.py tools/extract_sentry.py tools/extract_hazard.py tools/extract_pickup.py tools/extract_emerge.py tools/extract_wisp.py tools/extract_zombie.py tools/extract_thrower.py tools/extract_boss.py tools/extract_boss_motion.py reference/constructors.json assets/board.json | .venv/bin/python
	.venv/bin/python tools/extract.py
assets: .venv/bin/python
	.venv/bin/python tools/extract.py
test: all
	.venv/bin/python tests/test_assets.py
	.venv/bin/python tests/test_runtime.py
	.venv/bin/python tools/check_sprite_render.py
	.venv/bin/python tests/test_animation.py
	.venv/bin/python tests/test_actor_contract.py
	.venv/bin/python tests/test_contact.py
	.venv/bin/python tests/test_damage.py
	.venv/bin/python tests/test_damage_runtime.py
	.venv/bin/python tests/test_weapon_runtime.py
	.venv/bin/python tests/test_zombie.py
	.venv/bin/python tests/test_zombie_runtime.py
	.venv/bin/python tests/test_thrower.py
	.venv/bin/python tests/test_thrower_runtime.py
	.venv/bin/python tests/test_missile_contact.py
	.venv/bin/python tests/test_missile_runtime.py
	.venv/bin/python tests/test_boss_layers.py
	.venv/bin/python tests/test_boss_motion.py
	.venv/bin/python tests/test_boss_layers_runtime.py
	.venv/bin/python tests/test_wisp.py
	.venv/bin/python tests/test_wisp_runtime.py
	.venv/bin/python tests/test_emerge.py
	.venv/bin/python tests/test_emerge_runtime.py
	.venv/bin/python tests/test_pickup.py
	.venv/bin/python tests/test_pickup_runtime.py
	.venv/bin/python tests/test_hazard.py
	.venv/bin/python tests/test_hazard_runtime.py
	.venv/bin/python tests/test_sentry.py
	.venv/bin/python tests/test_sentry_runtime.py
	.venv/bin/python tests/test_loot.py
	.venv/bin/python tests/test_loot_runtime.py
	.venv/bin/python tests/test_skeleton.py
	.venv/bin/python tests/test_skeleton_runtime.py
	.venv/bin/python tests/test_world.py
	.venv/bin/python tests/test_hidden_runtime.py
	.venv/bin/python tests/test_npc_runtime.py
clean:
	$(MAKE) -f $(GDK)/makefile.gen JAVA=$(JAVA) clean
