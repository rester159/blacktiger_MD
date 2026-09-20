local m=manager.machine;local cpu=m.devices[':maincpu'];local dbg=m.debugger
local p=cpu.spaces.program;local out=assert(io.open('events.txt','w'))
local function le(a,v) p:write_u8(a,v&255);p:write_u8(a+1,(v>>8)&255) end
local function call(pc,finish)
 cpu.state.SP.value=0xeffe;le(0xeffe,0x1e17);cpu.state.PC.value=pc
 dbg:command('bpclear');dbg:command(string.format('bp %04x:maincpu,1',finish));cpu.debug:go()
 repeat emu.wait_next_update() until dbg.execution_state=='stop'
 assert(cpu.state.PC.value==finish)
end
assert(dbg and cpu.state.PC.value==0);dbg.visible_cpu=cpu
for id,c in ipairs(dofile('cases.lua')) do
 for a=0xe000,0xffff do p:write_u8(a,0) end
 le(0xe160,0xe150);le(0xe140,0xe100)
 p:write_u8(0xe915,c.poison);p:write_u8(0xe919,c.gate);p:write_u8(0xe028,c.reverse);p:write_u8(0xf3b0,c.antidotes);p:write_u8(0xf3ae,c.antidotes//10);p:write_u8(0xf3af,c.antidotes%10)
 p:write_u8(0xe905,c.invincible);cpu.state.IX.value=0xf940;p:write_u8(0xf94d,0xa6)
 p:write_u8(0xf40e,4);p:write_u8(0xf3ad,2)
 local hurt=c.poison_contact==1 or (c.poison_contact==2 and c.gate==0 and c.antidotes==0)
 call(c.poison_contact==2 and 0x4847 or c.poison_contact==1 and 0x3543 or 0x4872,hurt and 0x354e or 0x31e8)
 out:write(string.format('CONTACT|%d|%d|%d|%d|%d|%d|%d|%d\n',id-1,p:read_u8(0xe919),p:read_u8(0xe028),p:read_u8(0xf3b0),p:read_u8(0xf40e),p:read_u8(0xf3ad),p:read_u8(0xe915),hurt and 1 or 0))
end
cpu.spaces.io:write_u8(1,7);p:write_u8(0xe0e3,7)
for gate=0,60 do
 p:write_u8(0xe919,gate);call(0x80bb,0x80c3)
 out:write(string.format('TICK|%d|%d\n',gate,p:read_u8(0xe919)))
end
out:write('COMPLETE\n');out:close();m:exit()
