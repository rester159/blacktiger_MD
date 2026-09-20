local m=manager.machine;local cpu=m.devices[':maincpu'];local dbg=m.debugger;local p=cpu.spaces.program
local out=assert(io.open('events.txt','w'))
local function le(a,v) p:write_u8(a,v&255);p:write_u8(a+1,(v>>8)&255) end
local function be(a,v) p:write_u8(a,(v>>8)&255);p:write_u8(a+1,v&255) end
assert(dbg and cpu.state.PC.value==0);dbg.visible_cpu=cpu
for id,c in ipairs(dofile('cases.lua')) do
 for a=0xe000,0xffff do p:write_u8(a,0) end
 cpu.spaces.io:write_u8(1,6);p:write_u8(0xe0e3,6)
 p:write_u8(0xf3a1,c.round);p:write_u8(0xe0e7,c.wide);be(0xe030,c.x);be(0xe032,c.y)
 p:write_u8(0xe900,c.player);cpu.state.SP.value=0xeffe;le(0xeffe,0x1e17);cpu.state.PC.value=0x2532
 dbg:command('bpclear');dbg:command('bp 1e17:maincpu,1');cpu.debug:go()
 repeat emu.wait_next_update() until dbg.execution_state=='stop'
 local a=0xe058+c.player*4
 out:write(string.format('CHECKPOINT|%d|%d|%d\n',id-1,p:read_u8(a)*256+p:read_u8(a+1),p:read_u8(a+2)*256+p:read_u8(a+3)))
end
out:write('COMPLETE\n');out:close();m:exit()
