local m=manager.machine;local cpu=m.devices[':maincpu'];local dbg=m.debugger
local p=cpu.spaces.program;local ports=cpu.spaces.io
local out=assert(io.open('events.txt','w'))
local function le(a,v)p:write_u8(a,v&255);p:write_u8(a+1,(v>>8)&255)end
local function hex(a,n)local t={} for i=0,n-1 do t[#t+1]=string.format('%02x',p:read_u8(a+i))end return table.concat(t)end
assert(cpu.state.PC.value==0);dbg.visible_cpu=cpu
for id,c in ipairs(dofile('cases.lua'))do
 for a=0xe000,0xffff do p:write_u8(a,0)end
 ports:write_u8(1,7);p:write_u8(0xe0e3,7)
 p:write_u8(0xf400,64);p:write_u8(0xf43d,1);le(0xf43e,0x9c07)
 p:write_u8(0xf41e,c.profile//2);p:write_u8(0xf41f,c.profile%2);p:write_u8(0xe901,(c.profile%2)*4)
 p:write_u8(0xffef,c.x);p:write_u8(0xffee,c.y)
 for tick=1,329 do
  le(0xe160,0xe150);le(0xe140,0xe100);cpu.state.SP.value=0xeffe;cpu.state.PC.value=0x8446
  dbg:command('bpclear');dbg:command('bp 85bc:maincpu,1');dbg:command('bp 2013:maincpu,1');cpu.debug:go()
  repeat emu.wait_next_update() until dbg.execution_state=='stop'
  out:write(string.format('TICK|%d|%d|%d|%s|%s\n',id-1,tick,p:read_u8(0xf43d),hex(0xffec,16),hex(0xffd4,16)))
  assert((cpu.state.PC.value==0x2013)==(tick==329))
 end
end
out:write('COMPLETE\n');out:close();m:exit()
