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
 for _,r in ipairs({'AF','BC','DE','HL','IX','IY'}) do cpu.state[r].value=0 end
 ports:write_u8(1,2);p:write_u8(0xe0e3,2)
 for i=0,31 do p:write_u8(0xf520+i,p:read_u8(c.template+i)) end
 be(0xf521,c.x);be(0xf523,96);be(0xf53a,0xfe28)
 for tick=1,64 do
  if p:read_u8(0xf520)~=0 then cpu.state.IX.value=0xf520;call(0x2fe7) end
  local a={};for i=0,31 do a[#a+1]=string.format('%02x',p:read_u8(0xf520+i)) end
  out:write(string.format('SHOT|%d|%d|%s|%d\n',id-1,tick,table.concat(a),p:read_u8(0xfe28)))
 end
end
out:write('COMPLETE\n');out:close();m:exit()
