local m=manager.machine;local cpu=m.devices[':maincpu'];local dbg=m.debugger
local p=cpu.spaces.program;local out=assert(io.open('events.txt','w'))
local function le(a,v)p:write_u8(a,v&255);p:write_u8(a+1,(v>>8)&255)end
local function be(a,v)p:write_u8(a,(v>>8)&255);p:write_u8(a+1,v&255)end
local function hex(a,n)local t={}for i=0,n-1 do t[#t+1]=string.format('%02x',p:read_u8(a+i))end return table.concat(t)end
assert(cpu.state.PC.value==0);dbg.visible_cpu=cpu
for id,c in ipairs(dofile('cases.lua'))do
 for a=0xe000,0xffff do p:write_u8(a,0)end
 for i=0,31 do p:write_u8(0xea00+i,p:read_u8(0x7a6b+c.profile*32+i))end
 be(0xea01,c.x);be(0xea03,c.y);be(0xea1a,0xff00)
 for tick=1,180 do
  if p:read_u8(0xea00)~=0 then
   cpu.state.IX.value=0xea00;cpu.state.SP.value=0xeffc;le(0xeffc,0x1e17);cpu.state.PC.value=0x2fe7
   dbg:command('bpclear');dbg:command('bp 1e17:maincpu,1');cpu.debug:go()
   repeat emu.wait_next_update() until dbg.execution_state=='stop'
  end
  out:write(string.format('TICK|%d|%d|%s|%s\n',id-1,tick,hex(0xea00,32),hex(0xff00,4)))
 end
end
out:write('COMPLETE\n');out:close();m:exit()
