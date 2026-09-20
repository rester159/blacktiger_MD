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
 for name in ('bdu-01a.5e','bdu-02a.6e','bdu-03a.8e'):
  b=(source/name).read_bytes()
  for at in range(0,len(b)-255,256):
   part=b[at:at+256]
   if len(set(part))<32:continue
   assert part not in raw,(name,hex(at));checked+=1
assets=json.loads((ROOT/'reports/asset-tests.json').read_text());tests=json.loads((ROOT/'reports/runtime-tests.json').read_text());assert tests['rom_sha256']==sha(rom)
npc=json.loads((ROOT/'reports/npc-runtime-tests.json').read_text());assert npc['passed'] and npc['rom_sha256']==sha(rom)
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
report={'crawler_checks':crawler,'crawler_runtime_checks':crawler_runtime,'statue_shell_checks':statue_shell,'statue_runtime_checks':statue_runtime,'statue_body_checks':statue,'checkpoint_checks':checkpoint,'checkpoint_runtime_checks':checkpoint_runtime,'restart_checks':restart,'progress_checks':progress,'progress_runtime_checks':progress_runtime,'shop_checks':shop,'shop_runtime_checks':shop_runtime,'container_trap_checks':container_trap,'container_open_checks':container_open,'container_contact_checks':container_contact,'container_checks':container,'container_runtime_checks':container_runtime,'projectile_edge_checks':projectile_edges,'projectile_edge_runtime_checks':projectile_edge_runtime,'spitter_checks':spitter,'spitter_runtime_checks':spitter_runtime,'dagger_actor_checks':dagger,'dagger_actor_runtime_checks':dagger_runtime,'pair_checks':pair,'pair_runtime_checks':pair_runtime,'screen_attack_checks':screen_attack,'boulder_checks':boulder,'boulder_runtime_checks':boulder_runtime,'stone_runtime_checks':stone_runtime,'boss_upper_checks':boss_upper,'boss_upper_runtime_checks':boss_upper_runtime,'boss_motion_checks':boss_motion,'boss_layer_checks':boss_layers,'boss_layer_runtime_checks':boss_runtime,'missile_runtime_checks':missile_runtime,'missile_contact_checks':missile_contact,'thrower_source_checks':thrower,'thrower_runtime_checks':thrower_runtime,'weapon_runtime_checks':weapon,'zombie_source_checks':zombie,'zombie_runtime_checks':zombie_runtime,'damage_source_checks':damage,'damage_runtime_checks':damage_runtime,'contact_source_checks':contact,'wisp_source_checks':wisp_trace,'emerge_source_checks':emerge_trace,'sprite_render_checks':sprites,'pickup_source_checks':pickup_trace,'hazard_source_checks':hazard_trace,'sentry_source_checks':sentry_trace,'loot_cartridge_cases':len(loot['cases']),'loot_source_checks':loot_trace,'skeleton_variants':len(skeleton['variants']),'skeleton_trace_ticks':sk_trace['tick_comparisons'],'hidden_wall_cases':hidden['wall_cases'],'hidden_reward_kinds':hidden['reward_kinds'],'sparse_terrain_states':world['map_and_collision_states'],'actor_initial_state_checks':actors,'npc_variants_passed':len(npc['variants']),'source_animation_trace_comparisons':anim['original_trace_comparisons'],'status':'development prototype; complete port not achieved','rom':'blacktiger_astra.bin','rom_bytes':len(raw),'rom_sha256':sha(rom),'checksum':checksum,'asset_checks_passed':assets['passed'],'runtime_checks_passed':tests['passed'],'full_rate_all_routes':tests['full_rate_all_routes'],'cadence':tests['cadence'],'arcade_program_chunk_audit':{'chunks_checked':checked,'embedded_matches':0,'limitation':'Supporting check, not a formal proof of the entire runtime call graph.'},'native_sources':{str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'src').glob('*.c'))},'build_command':'make test && python3 tools/package.py','limitations':['Unverified and provisional actor/boss behaviors and graphics mappings','Original music missing; native PSG placeholder effects','No full natural playthrough or real-hardware validation','NTSC cadence shortfalls; PAL unverified']}
out=ROOT/'dist';out.mkdir(exist_ok=True);shutil.copyfile(rom,out/'blacktiger_astra.bin');shutil.copyfile(ROOT/'out/release/symbol.txt',out/'symbols.txt');(out/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('rom_bytes','rom_sha256','asset_checks_passed','runtime_checks_passed','full_rate_all_routes')}))
