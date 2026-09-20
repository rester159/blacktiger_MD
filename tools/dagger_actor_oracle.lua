local m=manager.machine;local cpu=m.devices[':maincpu'];local dbg=m.debugger
local p=cpu.spaces.program;local ports=cpu.spaces.io
local out=assert(io.open('events.txt','w'))
local function le(a,v) p:write_u8(a,v&255);p:write_u8(a+1,(v>>8)&255) end
local function be(a,v) p:write_u8(a,(v>>8)&255);p:write_u8(a+1,v&255) end
local function call(pc)
 cpu.state.SP.value=0xeffe;le(0xeffe,0x1e17);cpu.state.PC.value=pc
 dbg:command('bpclear');dbg:command('bp 1e17:maincpu,1');cpu.debug:go()
 repeat emu.wait_next_update() until dbg.execution_state=='stop'
end
assert(dbg and cpu.state.PC.value==0);dbg.visible_cpu=cpu
for id,c in ipairs(dofile('cases.lua')) do
 for a=0xe000,0xffff do p:write_u8(a,0) end
 ports:write_u8(1,0);p:write_u8(0xe0e3,0);le(0xe160,0xe150);le(0xe140,0xe100);p:write_u8(0xe010,1)
 local at=c.pool==32 and 0xf520 or 0xf940
 p:write_u8(at,0x80);be(at+1,c.x);be(at+3,c.y);p:write_u8(at+10,100);p:write_u8(at+14,100)
 p:write_u8(at+16,c.w);p:write_u8(at+17,c.h);be(at+26,0xfeac);le(at+24,0xec58)
 p:write_u8(0xf400,0x80);be(0xf401,400);be(0xf403,400);p:write_u8(0xf40d,c.damage)
 p:write_u8(0xfca0,0x80);be(0xfca1,c.sx);be(0xfca3,c.sy);p:write_u8(0xfcb0,4);p:write_u8(0xfcb1,2)
 p:write_u8(0xe003,c.parity);cpu.state.IX.value=at
 call(c.pool==32 and 0x2fe7 or 0x32c7)
 out:write(string.format('HIT|%d|%d|%d\n',id-1,p:read_u8(at+14),p:read_u8(0xfca0)))
end
out:write('COMPLETE\n');out:close();m:exit()
