local m=manager.machine;local cpu=m.devices[':maincpu'];local dbg=m.debugger;local p=cpu.spaces.program
local out=assert(io.open('events.txt','w'))
local function le(a,v) p:write_u8(a,v&255);p:write_u8(a+1,(v>>8)&255) end
local function call(pc,stop)
 cpu.state.SP.value=0xeffe;le(0xeffe,0x1e17);cpu.state.PC.value=pc
 dbg:command('bpclear');dbg:command('bp '..string.format('%x',stop or 0x1e17)..':maincpu,1');cpu.debug:go()
 repeat emu.wait_next_update() until dbg.execution_state=='stop'
end
local function digits(a,n,v) for i=n-1,0,-1 do p:write_u8(a+i,v%10);v=v//10 end end
assert(dbg and cpu.state.PC.value==0);dbg.visible_cpu=cpu
call(0x11f2,0x121c);call(0x12f2,0x1310);cpu.state.IY.value=0xf3c0;call(0x224e,0x226f);call(0x22eb,0x22fe)
out:write(string.format('INITIAL|%d|%d|%d|%d|%d|%d\n',p:read_u8(0xf3a0),p:read_u8(0xf3b6),p:read_u8(0xf40e),p:read_u16(0xf3a7),p:read_u8(0xf3ad),p:read_u8(0xf3ab)))
for id,c in ipairs(dofile('cases.lua')) do
 for a=0xe000,0xffff do p:write_u8(a,0) end
 p:write_u8(0xe010,128);p:write_u8(0xe144,16);p:write_u8(0xf3b6,c.maximum);p:write_u8(0xf40e,1)
 le(0xf3b4,0x13be+(c.maximum-1)*8);digits(0xe1e8,8,c.score)
 call(0x14f7)
 local score=0;for a=0xe1e8,0xe1ef do score=score*10+p:read_u8(a) end
 out:write(string.format('SCORE|%d|%d|%d|%d\n',id-1,score,p:read_u8(0xf3b6),p:read_u8(0xf40e)))
end
out:write('COMPLETE\n');out:close();m:exit()
