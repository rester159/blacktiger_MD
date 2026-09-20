local m=manager.machine;local cpu=m.devices[':maincpu'];local dbg=m.debugger
local p=cpu.spaces.program;local out=assert(io.open('events.txt','w'))
local function le(a,v) p:write_u8(a,v&255);p:write_u8(a+1,(v>>8)&255) end
local function call(pc)
 cpu.state.IX.value=0xf800;cpu.state.SP.value=0xeffe;le(0xeffe,0x1e17);cpu.state.PC.value=pc
 dbg:command('bpclear');dbg:command('bp 1e17:maincpu,1');cpu.debug:go()
 repeat emu.wait_next_update() until dbg.execution_state=='stop'
end
assert(dbg and cpu.state.PC.value==0);dbg.visible_cpu=cpu
for id,c in ipairs(dofile('cases.lua')) do
 for a=0xe000,0xffff do p:write_u8(a,0) end
 le(0xf818,0xea00);le(0xf81c,0xb247);le(0xf81e,0xb215)
 p:write_u8(0xf80c,9);p:write_u8(0xf80a,37)
 p:write_u8(0xea01,c.opened);p:write_u8(0xea02,c.collected)
 p:write_u8(0xf3ab,c.keys);p:write_u8(0xf3a9,c.keys//10);p:write_u8(0xf3aa,c.keys%10)
 le(0xf3a7,c.coins);p:write_u8(0xf40e,c.hp);p:write_u8(0xf3b6,c.max_hp);p:write_u8(0xf421,c.invincible)
 call(c.pc)
 out:write(string.format('CONTACT|%d|%d|%d|%d|%d|%d|%d|%d|%d|%d|%d\n',id-1,p:read_u8(0xf3ab),p:read_u8(0xea01),p:read_u8(0xea02),p:read_u16(0xf3a7),p:read_u8(0xf40e),p:read_u8(0xf421),p:read_u8(0xf80c),p:read_u8(0xf80a),p:read_u16(0xf81e),p:read_u8(0xf3a9)*10+p:read_u8(0xf3aa)))
end
out:write('COMPLETE\n');out:close();m:exit()
