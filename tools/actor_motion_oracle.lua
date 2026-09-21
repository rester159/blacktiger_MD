local m=manager.machine;local cpu=m.devices[':maincpu'];local dbg=m.debugger;local p=cpu.spaces.program
local out=assert(io.open('events.txt','w'))
local function le(a,v)p:write_u8(a,v&255);p:write_u8(a+1,(v>>8)&255)end
local function be(a,v)p:write_u8(a,(v>>8)&255);p:write_u8(a+1,v&255)end
assert(cpu.state.PC.value==0);dbg.visible_cpu=cpu
for id,c in ipairs(dofile('cases.lua'))do
 for a=0xe000,0xffff do p:write_u8(a,0)end
 cpu.spaces.io:write_u8(1,0);p:write_u8(0xe0e3,0)
 p:write_u8(0xf940,128);be(0xf941,c.x);be(0xf943,c.y);p:write_u8(0xf946,c.vx&255);p:write_u8(0xf947,c.vy&255)
 p:write_u8(0xf94c,c.mode);le(0xf958,0xec58);p:write_u8(0xec58,c.persistence)
 cpu.state.IX.value=0xf940;cpu.state.IY.value=0xfeac;cpu.state.SP.value=0xeffe;le(0xeffe,0x1e17);cpu.state.PC.value=0x3351
 dbg:command('bpclear');dbg:command('bp 1e17:maincpu,1');cpu.debug:go()
 repeat emu.wait_next_update()until dbg.execution_state=='stop'
 out:write(string.format('CASE|%d|%d|%d|%d|%d\n',id-1,p:read_u8(0xf940),p:read_u8(0xf941)*256+p:read_u8(0xf942),p:read_u8(0xf943)*256+p:read_u8(0xf944),p:read_u8(0xec58)))
end
out:write('COMPLETE\n');out:close();m:exit()
