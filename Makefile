JAVA ?= $(or $(wildcard /opt/homebrew/opt/openjdk/bin/java),java)
GDK ?= $(HOME)/mars/m68k-elf
.DEFAULT_GOAL := all
.PHONY: all assets test clean
all: src/hud_data.inc res/generated/object_patterns.bin src/ui_data.inc src/intro_data.inc
	$(MAKE) -f $(GDK)/makefile.gen JAVA=$(JAVA) LIBGCC="$(shell $(GDK)/bin/m68k-elf-gcc -m68000 -print-libgcc-file-name)"
	python3 tools/finalize_rom.py out/release/rom.bin
.venv/bin/python: requirements.txt
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt
res/generated/object_patterns.bin: tools/hud_assets.py reference/hud_oracle_events.txt tools/extract.py tools/extract_npc_sequence.py reference/npc_sequence_oracle.json reference/npc_sequence_oracle_events.txt tools/extract_sfx.py reference/sfx_oracle.json reference/sfx_oracle_events.txt tools/extract_ending.py reference/ending_oracle.json reference/ending_oracle_events.txt tools/extract_clear_screen.py reference/clear_screen_oracle.json reference/clear_screen_oracle_events.txt tools/extract_actor_dispatch.py tools/extract_bonus.py tools/extract_music.py $(wildcard reference/music/*.txt) tools/extract_armor_break.py tools/extract_player_death.py tools/extract_clear.py reference/clear_oracle.json reference/clear_oracle_events.txt tools/extract_player_dagger.py tools/arcade_source.py tools/extract_animation.py tools/actor_contract.py tools/extract_hidden.py tools/extract_skeleton.py tools/extract_loot.py tools/extract_sentry.py tools/extract_hazard.py tools/extract_pickup.py tools/extract_emerge.py tools/extract_wisp.py tools/extract_zombie.py tools/extract_thrower.py tools/extract_spitter.py tools/extract_boss.py tools/extract_boss_motion.py tools/extract_boulder.py tools/extract_pair.py tools/extract_container.py tools/extract_teleporter.py tools/extract_eruption.py tools/extract_waveboss.py tools/extract_flailer.py tools/extract_hunter.py tools/extract_crawler.py tools/extract_dragon_shot.py tools/extract_dragon.py tools/extract_reinforcement_body.py tools/extract_edge_actor.py tools/extract_statue.py tools/extract_checkpoint.py tools/extract_progress.py reference/progress_oracle.json tools/extract_shop.py reference/shop_oracle.json reference/constructors.json assets/board.json | .venv/bin/python
	.venv/bin/python tools/extract.py
assets: .venv/bin/python
	.venv/bin/python tools/extract.py
src/ui_data.inc: tools/build_ui.py assets/ui/title_arcade.png assets/board.json | .venv/bin/python
	.venv/bin/python tools/build_ui.py
test: all
	.venv/bin/python tests/test_hud_runtime.py
	.venv/bin/python tests/test_settings_runtime.py
	.venv/bin/python tests/test_frontend_runtime.py
	.venv/bin/python tests/test_boss_rush_runtime.py
	.venv/bin/python tests/test_presentation_runtime.py
	.venv/bin/python tests/test_sfx.py
	.venv/bin/python tests/test_sfx_runtime.py
	.venv/bin/python tests/test_ending.py
	.venv/bin/python tests/test_ending_runtime.py
	.venv/bin/python tests/test_clear_screen_runtime.py
	.venv/bin/python tests/test_controls_runtime.py
	.venv/bin/python tests/test_actor_dispatch.py
	.venv/bin/python tests/test_background_runtime.py
	.venv/bin/python tests/test_bonus.py
	.venv/bin/python tests/test_bonus_runtime.py
	.venv/bin/python tests/test_music_catalog_runtime.py
	.venv/bin/python tests/test_music_events_runtime.py
	.venv/bin/python tests/test_music.py
	.venv/bin/python tests/test_music_runtime.py
	.venv/bin/python tests/test_frame_scheduler.py
	.venv/bin/python tools/profile_runtime.py
	.venv/bin/python tests/test_armor_break.py
	.venv/bin/python tests/test_armor_break_runtime.py
	.venv/bin/python tests/test_game_over.py
	.venv/bin/python tests/test_game_over_runtime.py
	.venv/bin/python tests/test_round_clear.py
	.venv/bin/python tests/test_round_clear_runtime.py
	.venv/bin/python tests/test_player_death.py
	.venv/bin/python tests/test_player_death_runtime.py
	.venv/bin/python tests/test_posture_runtime.py
	.venv/bin/python tests/test_player_weapon_runtime.py
	.venv/bin/python tests/test_chain_actor.py
	.venv/bin/python tests/test_player_dagger.py
	.venv/bin/python tests/test_player_motion.py
	.venv/bin/python tests/test_player_motion_runtime.py
	.venv/bin/python tests/test_assets.py
	.venv/bin/python tests/test_runtime.py
	.venv/bin/python tools/check_sprite_render.py
	.venv/bin/python tests/test_animation.py
	.venv/bin/python tests/test_actor_contract.py
	.venv/bin/python tests/test_contact.py
	.venv/bin/python tests/test_dagger_actor.py
	.venv/bin/python tests/test_dagger_actor_runtime.py
	.venv/bin/python tests/test_damage.py
	.venv/bin/python tests/test_damage_runtime.py
	.venv/bin/python tests/test_weapon_runtime.py
	.venv/bin/python tests/test_zombie.py
	.venv/bin/python tests/test_zombie_runtime.py
	.venv/bin/python tests/test_thrower.py
	.venv/bin/python tests/test_thrower_runtime.py
	.venv/bin/python tests/test_spitter.py
	.venv/bin/python tests/test_spitter_runtime.py
	.venv/bin/python tests/test_missile_contact.py
	.venv/bin/python tests/test_missile_runtime.py
	.venv/bin/python tests/test_projectile_edges.py
	.venv/bin/python tests/test_projectile_edge_runtime.py
	.venv/bin/python tests/test_boss_layers.py
	.venv/bin/python tests/test_boss_motion.py
	.venv/bin/python tests/test_boss_motion.py --upper
	.venv/bin/python tests/test_boss_layers_runtime.py
	.venv/bin/python tests/test_boss_upper_runtime.py
	.venv/bin/python tests/test_stone_runtime.py
	.venv/bin/python tests/test_boulder.py
	.venv/bin/python tests/test_boulder_runtime.py
	.venv/bin/python tests/test_pair.py
	.venv/bin/python tests/test_pair_runtime.py
	.venv/bin/python tests/test_wisp.py
	.venv/bin/python tests/test_wisp_runtime.py
	.venv/bin/python tests/test_emerge.py
	.venv/bin/python tests/test_emerge_runtime.py
	.venv/bin/python tests/test_checkpoint.py
	.venv/bin/python tests/test_checkpoint_runtime.py
	.venv/bin/python tests/test_progress.py
	.venv/bin/python tests/test_progress_runtime.py
	.venv/bin/python tests/test_restart_runtime.py
	.venv/bin/python tests/test_status.py
	.venv/bin/python tests/test_wave.py
	.venv/bin/python tests/test_flailer.py
	.venv/bin/python tests/test_flailer_weapon.py
	.venv/bin/python tests/test_flailer_runtime.py
	.venv/bin/python tests/test_large_contact.py
	.venv/bin/python tests/test_dragon_wave.py
	.venv/bin/python tests/test_dragon_shot.py
	.venv/bin/python tests/test_dragon_contact.py
	.venv/bin/python tests/test_dragon_runtime.py
	.venv/bin/python tests/test_dragon.py
	.venv/bin/python tests/test_waveboss.py
	.venv/bin/python tests/test_waveboss_seed.py
	.venv/bin/python tests/test_waveboss_runtime.py
	.venv/bin/python tests/test_eruption.py
	.venv/bin/python tests/test_eruption_runtime.py
	.venv/bin/python tests/test_teleporter.py
	.venv/bin/python tests/test_teleporter_runtime.py
	.venv/bin/python tests/test_hunter.py
	.venv/bin/python tests/test_hunter_shell.py
	.venv/bin/python tests/test_hunter_runtime.py
	.venv/bin/python tests/test_reinforcement_body.py
	.venv/bin/python tests/test_reinforcement_shot.py
	.venv/bin/python tests/test_reinforcement_body_runtime.py
	.venv/bin/python tests/test_edge_actor.py
	.venv/bin/python tests/test_edge_shot.py
	.venv/bin/python tests/test_edge_actor_runtime.py
	.venv/bin/python tests/test_edge_spawn.py
	.venv/bin/python tests/test_edge_spawn_runtime.py
	.venv/bin/python tests/test_reinforcement.py
	.venv/bin/python tests/test_reinforcement_runtime.py
	.venv/bin/python tests/test_crawler.py
	.venv/bin/python tests/test_crawler_runtime.py
	.venv/bin/python tests/test_statue.py
	.venv/bin/python tests/test_statue_shell.py
	.venv/bin/python tests/test_statue_runtime.py
	.venv/bin/python tests/test_shop.py
	.venv/bin/python tests/test_shop_runtime.py
	.venv/bin/python tests/test_container_trap.py
	.venv/bin/python tests/test_container_open_runtime.py
	.venv/bin/python tests/test_container_contact.py
	.venv/bin/python tests/test_container.py
	.venv/bin/python tests/test_container_runtime.py
	.venv/bin/python tests/test_pickup.py
	.venv/bin/python tests/test_pickup_runtime.py
	.venv/bin/python tests/test_screen_attack_runtime.py
	.venv/bin/python tests/test_hazard.py
	.venv/bin/python tests/test_hazard_runtime.py
	.venv/bin/python tests/test_sentry.py
	.venv/bin/python tests/test_sentry_runtime.py
	.venv/bin/python tests/test_loot.py
	.venv/bin/python tests/test_loot_runtime.py
	.venv/bin/python tests/test_actor_motion.py
	.venv/bin/python tests/test_actor_motion_runtime.py
	.venv/bin/python tests/test_skeleton.py
	.venv/bin/python tests/test_skeleton_runtime.py
	.venv/bin/python tests/test_world.py
	.venv/bin/python tests/test_hidden_runtime.py
	.venv/bin/python tests/test_npc_sequence.py
	.venv/bin/python tests/test_npc_runtime.py
clean:
	$(MAKE) -f $(GDK)/makefile.gen JAVA=$(JAVA) clean

src/intro_data.inc: tools/build_intro.py reference/intro_oracle_events.txt.gz assets/board.json
	.venv/bin/python tools/build_intro.py

src/hud_data.inc: tools/build_hud.py tools/hud_assets.py reference/hud_oracle_events.txt res/generated/object_patterns.bin
	.venv/bin/python tools/build_hud.py
