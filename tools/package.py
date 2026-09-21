#!/usr/bin/env python3
"""Package only the exact cartridge that passed the recorded tests."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rom=ROOT/'out/release/rom.bin';raw=rom.read_bytes();assert raw[0x100:0x104]==b'SEGA'
checksum=sum(int.from_bytes(raw[i:i+2],'big') for i in range(0x200,len(raw),2))&65535
assert int.from_bytes(raw[0x18e:0x190],'big')==checksum
assert int.from_bytes(raw[0x1a4:0x1a8],'big')==len(raw)-1
source=ROOT.parent/'_capcom/black tiger/assets/source_packages/arcade/blktiger_supplied_romset_e54221c17ce6b5ee/payload'
checked=0
if source.exists():
 for name in ('bdu-01a.5e','bdu-02a.6e','bdu-03a.8e','bd-06.1l'):
  b=(source/name).read_bytes()
  for at in range(0,len(b)-255,256):
   part=b[at:at+256]
   if len(set(part))<32:continue
   assert part not in raw,(name,hex(at));checked+=1
controls=json.loads((ROOT/'reports/controls-runtime-tests.json').read_text());assert controls['passed'] and controls['rom_sha256']==sha(rom)
dispatch=json.loads((ROOT/'reports/actor-dispatch-tests.json').read_text());assert dispatch['passed'] and dispatch['rom_sha256']==sha(rom)
background=json.loads((ROOT/'reports/background-runtime-tests.json').read_text());assert background['passed'] and background['rom_sha256']==sha(rom)
bonus=json.loads((ROOT/'reports/bonus-runtime-tests.json').read_text());assert bonus['passed'] and bonus['rom_sha256']==sha(rom)
game_over=json.loads((ROOT/'reports/game-over-tests.json').read_text());assert game_over['passed']
game_over_runtime=json.loads((ROOT/'reports/game-over-runtime-tests.json').read_text());assert game_over_runtime['passed'] and game_over_runtime['rom_sha256']==sha(rom)
clear=json.loads((ROOT/'reports/round-clear-tests.json').read_text());assert clear['passed']
sfx=json.loads((ROOT/'reports/sfx-tests.json').read_text());assert sfx['passed']
sfx_runtime=json.loads((ROOT/'reports/sfx-runtime-tests.json').read_text());assert sfx_runtime['passed'] and sfx_runtime['rom_sha256']==sha(rom)
ending=json.loads((ROOT/'reports/ending-tests.json').read_text());assert ending['passed']
ending_runtime=json.loads((ROOT/'reports/ending-runtime-tests.json').read_text());assert ending_runtime['passed'] and ending_runtime['rom_sha256']==sha(rom)
clear_screen=json.loads((ROOT/'reports/clear-screen-runtime-tests.json').read_text());assert clear_screen['passed'] and clear_screen['rom_sha256']==sha(rom)
clear_runtime=json.loads((ROOT/'reports/round-clear-runtime-tests.json').read_text());assert clear_runtime['passed'] and clear_runtime['rom_sha256']==sha(rom)
bonus_source=json.loads((ROOT/'reports/bonus-tests.json').read_text());assert bonus_source['passed']
assets=json.loads((ROOT/'reports/asset-tests.json').read_text());tests=json.loads((ROOT/'reports/runtime-tests.json').read_text());assert tests['rom_sha256']==sha(rom)
npc_sequence=json.loads((ROOT/'reports/npc-sequence-tests.json').read_text());assert npc_sequence['passed']
npc=json.loads((ROOT/'reports/npc-runtime-tests.json').read_text());assert npc['passed'] and npc['rom_sha256']==sha(rom)
actor_motion=json.loads((ROOT/'reports/actor-motion-tests.json').read_text());assert actor_motion['passed']
actor_motion_runtime=json.loads((ROOT/'reports/actor-motion-runtime-tests.json').read_text());assert actor_motion_runtime['passed'] and actor_motion_runtime['rom_sha256']==sha(rom)
anim=json.loads((ROOT/'reports/animation-tests.json').read_text());assert anim['passed']
actors=json.loads((ROOT/'reports/actor-contract-tests.json').read_text());assert actors['passed'] and actors['rom_sha256']==sha(rom)
hidden=json.loads((ROOT/'reports/hidden-runtime-tests.json').read_text());assert hidden['passed'] and hidden['rom_sha256']==sha(rom)
world=json.loads((ROOT/'reports/world-tests.json').read_text());assert world['passed']
skeleton=json.loads((ROOT/'reports/skeleton-runtime-tests.json').read_text());assert skeleton['passed'] and skeleton['rom_sha256']==sha(rom)
sk_trace=json.loads((ROOT/'reports/skeleton-tests.json').read_text());assert sk_trace['passed']
loot=json.loads((ROOT/'reports/loot-runtime-tests.json').read_text());assert loot['passed'] and loot['rom_sha256']==sha(rom)
loot_trace=json.loads((ROOT/'reports/loot-tests.json').read_text());assert loot_trace['passed']
sentry=json.loads((ROOT/'reports/sentry-runtime-tests.json').read_text());assert sentry['passed'] and sentry['rom_sha256']==sha(rom)
sentry_trace=json.loads((ROOT/'reports/sentry-tests.json').read_text());assert sentry_trace['passed']
hazard=json.loads((ROOT/'reports/hazard-runtime-tests.json').read_text());assert hazard['passed'] and hazard['rom_sha256']==sha(rom)
hazard_trace=json.loads((ROOT/'reports/hazard-tests.json').read_text());assert hazard_trace['passed']
pickup=json.loads((ROOT/'reports/pickup-runtime-tests.json').read_text());assert pickup['passed'] and pickup['rom_sha256']==sha(rom)
pickup_trace=json.loads((ROOT/'reports/pickup-tests.json').read_text());assert pickup_trace['passed']
sprites=json.loads((ROOT/'reports/sprite-render-tests.json').read_text());assert sprites['passed'] and sprites['rom_sha256']==sha(rom)
emerge=json.loads((ROOT/'reports/emerge-runtime-tests.json').read_text());assert emerge['passed'] and emerge['rom_sha256']==sha(rom)
emerge_trace=json.loads((ROOT/'reports/emerge-tests.json').read_text());assert emerge_trace['passed']
wisp=json.loads((ROOT/'reports/wisp-runtime-tests.json').read_text());assert wisp['passed'] and wisp['rom_sha256']==sha(rom)
wisp_trace=json.loads((ROOT/'reports/wisp-tests.json').read_text());assert wisp_trace['passed']
contact=json.loads((ROOT/'reports/contact-tests.json').read_text());assert contact['passed']
damage=json.loads((ROOT/'reports/damage-tests.json').read_text());assert damage['passed']
damage_runtime=json.loads((ROOT/'reports/damage-runtime-tests.json').read_text());assert damage_runtime['passed'] and damage_runtime['rom_sha256']==sha(rom)
zombie=json.loads((ROOT/'reports/zombie-tests.json').read_text());assert zombie['passed']
zombie_runtime=json.loads((ROOT/'reports/zombie-runtime-tests.json').read_text());assert zombie_runtime['passed'] and zombie_runtime['rom_sha256']==sha(rom)
weapon=json.loads((ROOT/'reports/weapon-runtime-tests.json').read_text());assert weapon['passed'] and weapon['rom_sha256']==sha(rom)
thrower=json.loads((ROOT/'reports/thrower-tests.json').read_text());assert thrower['passed']
thrower_runtime=json.loads((ROOT/'reports/thrower-runtime-tests.json').read_text());assert thrower_runtime['passed'] and thrower_runtime['rom_sha256']==sha(rom)
missile_contact=json.loads((ROOT/'reports/missile-contact-tests.json').read_text());assert missile_contact['passed']
missile_runtime=json.loads((ROOT/'reports/missile-runtime-tests.json').read_text());assert missile_runtime['passed'] and missile_runtime['rom_sha256']==sha(rom)
boss_layers=json.loads((ROOT/'reports/boss-layer-tests.json').read_text());assert boss_layers['passed']
boss_runtime=json.loads((ROOT/'reports/boss-layer-runtime-tests.json').read_text());assert boss_runtime['passed'] and boss_runtime['rom_sha256']==sha(rom)
boss_motion=json.loads((ROOT/'reports/boss-motion-tests.json').read_text());assert boss_motion['passed']
boss_upper=json.loads((ROOT/'reports/boss-upper-motion-tests.json').read_text());assert boss_upper['passed']
boss_upper_runtime=json.loads((ROOT/'reports/boss-upper-runtime-tests.json').read_text());assert boss_upper_runtime['passed'] and boss_upper_runtime['rom_sha256']==sha(rom)
stone_runtime=json.loads((ROOT/'reports/stone-runtime-tests.json').read_text());assert stone_runtime['passed'] and stone_runtime['rom_sha256']==sha(rom)
boulder=json.loads((ROOT/'reports/boulder-tests.json').read_text());assert boulder['passed']
boulder_runtime=json.loads((ROOT/'reports/boulder-runtime-tests.json').read_text());assert boulder_runtime['passed'] and boulder_runtime['rom_sha256']==sha(rom)
screen_attack=json.loads((ROOT/'reports/screen-attack-runtime-tests.json').read_text());assert screen_attack['passed'] and screen_attack['rom_sha256']==sha(rom)
pair=json.loads((ROOT/'reports/pair-tests.json').read_text());assert pair['passed']
pair_runtime=json.loads((ROOT/'reports/pair-runtime-tests.json').read_text());assert pair_runtime['passed'] and pair_runtime['rom_sha256']==sha(rom)
dagger=json.loads((ROOT/'reports/dagger-actor-tests.json').read_text());assert dagger['passed']
dagger_runtime=json.loads((ROOT/'reports/dagger-actor-runtime-tests.json').read_text());assert dagger_runtime['passed'] and dagger_runtime['rom_sha256']==sha(rom)
spitter=json.loads((ROOT/'reports/spitter-tests.json').read_text());assert spitter['passed']
spitter_runtime=json.loads((ROOT/'reports/spitter-runtime-tests.json').read_text());assert spitter_runtime['passed'] and spitter_runtime['rom_sha256']==sha(rom)
projectile_edges=json.loads((ROOT/'reports/projectile-edge-tests.json').read_text());assert projectile_edges['passed']
projectile_edge_runtime=json.loads((ROOT/'reports/projectile-edge-runtime-tests.json').read_text());assert projectile_edge_runtime['passed'] and projectile_edge_runtime['rom_sha256']==sha(rom)
flailer=json.loads((ROOT/'reports/flailer-tests.json').read_text());assert flailer['passed']
flailer_weapon=json.loads((ROOT/'reports/flailer-weapon-tests.json').read_text());assert flailer_weapon['passed']
flailer_runtime=json.loads((ROOT/'reports/flailer-runtime-tests.json').read_text());assert flailer_runtime['passed'] and flailer_runtime['rom_sha256']==sha(rom)
large_contact=json.loads((ROOT/'reports/large-contact-tests.json').read_text());assert large_contact['passed']
posture_runtime=json.loads((ROOT/'reports/posture-runtime-tests.json').read_text());assert posture_runtime['passed'] and posture_runtime['rom_sha256']==sha(rom)
chain_actor=json.loads((ROOT/'reports/chain-actor-tests.json').read_text());assert chain_actor['passed']
player_dagger=json.loads((ROOT/'reports/player-dagger-tests.json').read_text());assert player_dagger['passed']
player_weapon_runtime=json.loads((ROOT/'reports/player-weapon-runtime-tests.json').read_text());assert player_weapon_runtime['passed'] and player_weapon_runtime['rom_sha256']==sha(rom)
player_motion=json.loads((ROOT/'reports/player-motion-tests.json').read_text());assert player_motion['passed']
player_motion_runtime=json.loads((ROOT/'reports/player-motion-runtime-tests.json').read_text());assert player_motion_runtime['passed'] and player_motion_runtime['rom_sha256']==sha(rom)
dragon_shot=json.loads((ROOT/'reports/dragon-shot-tests.json').read_text());assert dragon_shot['passed']
dragon_contact=json.loads((ROOT/'reports/dragon-contact-tests.json').read_text());assert dragon_contact['passed']
dragon_runtime=json.loads((ROOT/'reports/dragon-runtime-tests.json').read_text());assert dragon_runtime['passed'] and dragon_runtime['rom_sha256']==sha(rom)
dragon=json.loads((ROOT/'reports/dragon-tests.json').read_text());assert dragon['passed']
dragon_wave=json.loads((ROOT/'reports/dragon-wave-tests.json').read_text());assert dragon_wave['passed']
waveboss=json.loads((ROOT/'reports/waveboss-tests.json').read_text());assert waveboss['passed']
waveboss_seed=json.loads((ROOT/'reports/waveboss-seed-tests.json').read_text());assert waveboss_seed['passed']
waveboss_runtime=json.loads((ROOT/'reports/waveboss-runtime-tests.json').read_text());assert waveboss_runtime['passed'] and waveboss_runtime['rom_sha256']==sha(rom)
eruption=json.loads((ROOT/'reports/eruption-tests.json').read_text());assert eruption['passed']
eruption_runtime=json.loads((ROOT/'reports/eruption-runtime-tests.json').read_text());assert eruption_runtime['passed'] and eruption_runtime['rom_sha256']==sha(rom)
status_checks=json.loads((ROOT/'reports/status-tests.json').read_text());assert status_checks['passed']
wave=json.loads((ROOT/'reports/wave-tests.json').read_text());assert wave['passed']
teleporter_runtime=json.loads((ROOT/'reports/teleporter-runtime-tests.json').read_text());assert teleporter_runtime['passed'] and teleporter_runtime['rom_sha256']==sha(rom)
teleporter=json.loads((ROOT/'reports/teleporter-tests.json').read_text());assert teleporter['passed']
hunter_shell=json.loads((ROOT/'reports/hunter-shell-tests.json').read_text());assert hunter_shell['passed']
hunter_runtime=json.loads((ROOT/'reports/hunter-runtime-tests.json').read_text());assert hunter_runtime['passed'] and hunter_runtime['rom_sha256']==sha(rom)
hunter=json.loads((ROOT/'reports/hunter-tests.json').read_text());assert hunter['passed']
reinforcement_body=json.loads((ROOT/'reports/reinforcement-body-tests.json').read_text());assert reinforcement_body['passed']
reinforcement_shot=json.loads((ROOT/'reports/reinforcement-shot-tests.json').read_text());assert reinforcement_shot['passed']
reinforcement_body_runtime=json.loads((ROOT/'reports/reinforcement-body-runtime-tests.json').read_text());assert reinforcement_body_runtime['passed'] and reinforcement_body_runtime['rom_sha256']==sha(rom)
edge_actor=json.loads((ROOT/'reports/edge-actor-tests.json').read_text());assert edge_actor['passed']
edge_shot=json.loads((ROOT/'reports/edge-shot-tests.json').read_text());assert edge_shot['passed']
edge_actor_runtime=json.loads((ROOT/'reports/edge-actor-runtime-tests.json').read_text());assert edge_actor_runtime['passed'] and edge_actor_runtime['rom_sha256']==sha(rom)
edge_spawn=json.loads((ROOT/'reports/edge-spawn-tests.json').read_text());assert edge_spawn['passed']
edge_spawn_runtime=json.loads((ROOT/'reports/edge-spawn-runtime-tests.json').read_text());assert edge_spawn_runtime['passed'] and edge_spawn_runtime['rom_sha256']==sha(rom)
reinforcement=json.loads((ROOT/'reports/reinforcement-tests.json').read_text());assert reinforcement['passed']
reinforcement_runtime=json.loads((ROOT/'reports/reinforcement-runtime-tests.json').read_text());assert reinforcement_runtime['passed'] and reinforcement_runtime['rom_sha256']==sha(rom)
crawler=json.loads((ROOT/'reports/crawler-tests.json').read_text());assert crawler['passed']
crawler_runtime=json.loads((ROOT/'reports/crawler-runtime-tests.json').read_text());assert crawler_runtime['passed'] and crawler_runtime['rom_sha256']==sha(rom)
statue_shell=json.loads((ROOT/'reports/statue-shell-tests.json').read_text());assert statue_shell['passed']
statue_runtime=json.loads((ROOT/'reports/statue-runtime-tests.json').read_text());assert statue_runtime['passed'] and statue_runtime['rom_sha256']==sha(rom)
statue=json.loads((ROOT/'reports/statue-tests.json').read_text());assert statue['passed']
checkpoint=json.loads((ROOT/'reports/checkpoint-tests.json').read_text());assert checkpoint['passed']
checkpoint_runtime=json.loads((ROOT/'reports/checkpoint-runtime-tests.json').read_text());assert checkpoint_runtime['passed'] and checkpoint_runtime['rom_sha256']==sha(rom)
restart=json.loads((ROOT/'reports/restart-runtime-tests.json').read_text());assert restart['passed'] and restart['rom_sha256']==sha(rom)
progress=json.loads((ROOT/'reports/progress-tests.json').read_text());assert progress['passed']
progress_runtime=json.loads((ROOT/'reports/progress-runtime-tests.json').read_text());assert progress_runtime['passed'] and progress_runtime['rom_sha256']==sha(rom)
shop=json.loads((ROOT/'reports/shop-tests.json').read_text());assert shop['passed']
shop_runtime=json.loads((ROOT/'reports/shop-runtime-tests.json').read_text());assert shop_runtime['passed'] and shop_runtime['rom_sha256']==sha(rom)
container_trap=json.loads((ROOT/'reports/container-trap-tests.json').read_text());assert container_trap['passed']
container_open=json.loads((ROOT/'reports/container-open-runtime-tests.json').read_text());assert container_open['passed'] and container_open['rom_sha256']==sha(rom)
container_contact=json.loads((ROOT/'reports/container-contact-tests.json').read_text());assert container_contact['passed']
container=json.loads((ROOT/'reports/container-tests.json').read_text());assert container['passed']
container_runtime=json.loads((ROOT/'reports/container-runtime-tests.json').read_text());assert container_runtime['passed'] and container_runtime['rom_sha256']==sha(rom)
player_death=json.loads((ROOT/'reports/player-death-tests.json').read_text());assert player_death['passed']
player_death_runtime=json.loads((ROOT/'reports/player-death-runtime-tests.json').read_text());assert player_death_runtime['passed'] and player_death_runtime['rom_sha256']==sha(rom)
armor_break=json.loads((ROOT/'reports/armor-break-tests.json').read_text());assert armor_break['passed']
armor_break_runtime=json.loads((ROOT/'reports/armor-break-runtime-tests.json').read_text());assert armor_break_runtime['passed'] and armor_break_runtime['rom_sha256']==sha(rom)
frontend_checks={}
for name in ('frontend-runtime-tests','boss-rush-runtime-tests','presentation-runtime-tests','settings-runtime-tests','hud-runtime-tests'):
 result=json.loads((ROOT/f'reports/{name}.json').read_text());assert result['passed'] and result['rom_sha256']==sha(rom),name
 frontend_checks[name]=result
performance=json.loads((ROOT/'reports/performance-profile.json').read_text());assert performance['rom_sha256']==sha(rom)
frame_scheduler=json.loads((ROOT/'reports/frame-scheduler-tests.json').read_text());assert frame_scheduler['passed'] and frame_scheduler['rom_sha256']==sha(rom)
music=json.loads((ROOT/'reports/music-tests.json').read_text());assert music['passed']
music_runtime=json.loads((ROOT/'reports/music-runtime-tests.json').read_text());assert music_runtime['passed'] and music_runtime['rom_sha256']==sha(rom)
music_events=json.loads((ROOT/'reports/music-events-runtime-tests.json').read_text());assert music_events['passed'] and music_events['rom_sha256']==sha(rom)
music_catalog=json.loads((ROOT/'reports/music-catalog-runtime-tests.json').read_text());assert music_catalog['passed'] and music_catalog['rom_sha256']==sha(rom)
report={'frontend_checks':frontend_checks,'sfx_checks':sfx,'sfx_runtime_checks':sfx_runtime,'ending_checks':ending,'ending_runtime_checks':ending_runtime,'clear_screen_runtime_checks':clear_screen,'controls_runtime_checks':controls,'game_over_checks':game_over,'game_over_runtime_checks':game_over_runtime,'round_clear_checks':clear,'round_clear_runtime_checks':clear_runtime,'actor_dispatch_checks':dispatch,'background_runtime_checks':background,'bonus_checks':bonus_source,'bonus_runtime_checks':bonus,'music_catalog_checks':music_catalog,'music_event_checks':music_events,'music_checks':music,'music_runtime_checks':music_runtime,'frame_scheduler_checks':frame_scheduler,'performance_profile':performance,'armor_break_checks':armor_break,'armor_break_runtime_checks':armor_break_runtime,'player_death_checks':player_death,'player_death_runtime_checks':player_death_runtime,'posture_runtime_checks':posture_runtime,'chain_actor_checks':chain_actor,'player_dagger_checks':player_dagger,'player_weapon_runtime_checks':player_weapon_runtime,'player_motion_checks':player_motion,'player_motion_runtime_checks':player_motion_runtime,'dragon_shot_checks':dragon_shot,'dragon_contact_checks':dragon_contact,'dragon_runtime_checks':dragon_runtime,'dragon_body_checks':dragon,'dragon_wave_checks':dragon_wave,'edge_actor_checks':edge_actor,'edge_shot_checks':edge_shot,'edge_actor_runtime_checks':edge_actor_runtime,'edge_spawn_checks':edge_spawn,'edge_spawn_runtime_checks':edge_spawn_runtime,'reinforcement_body_checks':reinforcement_body,'reinforcement_shot_checks':reinforcement_shot,'reinforcement_body_runtime_checks':reinforcement_body_runtime,'reinforcement_checks':reinforcement,'reinforcement_runtime_checks':reinforcement_runtime,'flailer_checks':flailer,'flailer_weapon_checks':flailer_weapon,'flailer_runtime_checks':flailer_runtime,'large_contact_checks':large_contact,'waveboss_checks':waveboss,'waveboss_seed_checks':waveboss_seed,'waveboss_runtime_checks':waveboss_runtime,'eruption_checks':eruption,'eruption_runtime_checks':eruption_runtime,'status_checks':status_checks,'wave_checks':wave,'teleporter_runtime_checks':teleporter_runtime,'teleporter_body_checks':teleporter,'hunter_shell_checks':hunter_shell,'hunter_runtime_checks':hunter_runtime,'hunter_body_checks':hunter,'crawler_checks':crawler,'crawler_runtime_checks':crawler_runtime,'statue_shell_checks':statue_shell,'statue_runtime_checks':statue_runtime,'statue_body_checks':statue,'checkpoint_checks':checkpoint,'checkpoint_runtime_checks':checkpoint_runtime,'restart_checks':restart,'progress_checks':progress,'progress_runtime_checks':progress_runtime,'shop_checks':shop,'shop_runtime_checks':shop_runtime,'container_trap_checks':container_trap,'container_open_checks':container_open,'container_contact_checks':container_contact,'container_checks':container,'container_runtime_checks':container_runtime,'projectile_edge_checks':projectile_edges,'projectile_edge_runtime_checks':projectile_edge_runtime,'spitter_checks':spitter,'spitter_runtime_checks':spitter_runtime,'dagger_actor_checks':dagger,'dagger_actor_runtime_checks':dagger_runtime,'pair_checks':pair,'pair_runtime_checks':pair_runtime,'screen_attack_checks':screen_attack,'boulder_checks':boulder,'boulder_runtime_checks':boulder_runtime,'stone_runtime_checks':stone_runtime,'boss_upper_checks':boss_upper,'boss_upper_runtime_checks':boss_upper_runtime,'boss_motion_checks':boss_motion,'boss_layer_checks':boss_layers,'boss_layer_runtime_checks':boss_runtime,'missile_runtime_checks':missile_runtime,'missile_contact_checks':missile_contact,'thrower_source_checks':thrower,'thrower_runtime_checks':thrower_runtime,'weapon_runtime_checks':weapon,'zombie_source_checks':zombie,'zombie_runtime_checks':zombie_runtime,'damage_source_checks':damage,'damage_runtime_checks':damage_runtime,'contact_source_checks':contact,'wisp_source_checks':wisp_trace,'emerge_source_checks':emerge_trace,'sprite_render_checks':sprites,'pickup_source_checks':pickup_trace,'hazard_source_checks':hazard_trace,'sentry_source_checks':sentry_trace,'loot_cartridge_cases':len(loot['cases']),'loot_source_checks':loot_trace,'skeleton_variants':len(skeleton['variants']),'skeleton_trace_ticks':sk_trace['tick_comparisons'],'hidden_wall_cases':hidden['wall_cases'],'hidden_reward_kinds':hidden['reward_kinds'],'sparse_terrain_states':world['map_and_collision_states'],'actor_initial_state_checks':actors,'npc_variants_passed':len(npc['variants']),'source_animation_trace_comparisons':anim['original_trace_comparisons'],'status':'development prototype; complete port not achieved','rom':'blacktiger_astra.bin','rom_bytes':len(raw),'rom_sha256':sha(rom),'checksum':checksum,'asset_checks_passed':assets['passed'],'runtime_checks_passed':tests['passed'],'full_rate_all_routes':tests['full_rate_all_routes'],'cadence':tests['cadence'],'arcade_program_chunk_audit':{'chunks_checked':checked,'embedded_matches':0,'limitation':'Supporting check, not a formal proof of the entire runtime call graph.'},'native_sources':{str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'src').glob('*.c'))},'build_command':'make test && python3 tools/package.py','limitations':['Screen-edge collision behavior, some compound-boss geometry, impact presentation and global scheduling remain incomplete','25 FM tracks and 36 native PSG effect programs; remaining event bindings, command-queue behavior and hardware audio fidelity incomplete','Alternate-area transitions and animated terrain integrated; source transition presentation and whole-board scheduling unfinished','No full natural playthrough or real-hardware validation','NTSC cadence shortfalls; PAL unverified']}
out=ROOT/'dist';out.mkdir(exist_ok=True);shutil.copyfile(ROOT/'reports/music-preview.wav',out/'music-preview.wav');shutil.copyfile(rom,out/'blacktiger_astra.bin');shutil.copyfile(ROOT/'out/release/symbol.txt',out/'symbols.txt');(out/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('rom_bytes','rom_sha256','asset_checks_passed','runtime_checks_passed','full_rate_all_routes')}))
