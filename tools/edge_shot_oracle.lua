local m=manager.machine;local cpu=m.devices[':maincpu'];local dbg=m.debugger
local p=cpu.spaces.program;local ports=cpu.spaces.io
local out=assert(io.open('events.txt','w'))
local function emit(s) out:write(s,'\n');out:flush() end
local function le(a,v) p:write_u8(a,v&255);p:write_u8(a+1,(v>>8)&255) end
local function be(a,v) p:write_u8(a,(v>>8)&255);p:write_u8(a+1,v&255) end
local function hex(a,n) local t={} for i=0,n-1 do t[#t+1]=string.format('%02x',p:read_u8(a+i)) end return table.concat(t) end
local function call(pc)
 cpu.state.SP.value=0xeffe;le(0xeffe,0x1e17);cpu.state.PC.value=pc
 dbg:command('bpclear');dbg:command('bp 1e17:maincpu,1');dbg:command('bp 5a4f:maincpu,1');cpu.debug:go()
 repeat emu.wait_next_update() until dbg.execution_state=='stop'
 return cpu.state.PC.value==0x1e17
end
local data=dofile('cases.lua');assert(dbg and cpu.state.PC.value==0);dbg.visible_cpu=cpu
for id,c in ipairs(data.cases) do
 for a=0xe000,0xffff do p:write_u8(a,0) end
 for _,r in ipairs({'AF','BC','DE','HL','IX','IY'}) do cpu.state[r].value=0 end
 ports:write_u8(1,4);p:write_u8(0xe0e3,4);ports:write_u8(14,1);p:write_u8(0xe0e7,1)
 le(0xe160,0xe150);le(0xe140,0xe100)
 for bank=0,3 do
  ports:write_u8(13,bank)
  for at=0,4094,2 do
   local n=(bank*4096+at)//2;local x=((n&15)|((n>>4)&0x70))*16
   local tile=(c.wall==1 and x>=160) and data.solid or data.empty
   p:write_u8(0xc000+at,tile&255);p:write_u8(0xc001+at,(tile>>8)&7)
  end
 end
 for i=0,31 do p:write_u8(0xf520+i,p:read_u8(c.template+i)) end
 be(0xf521,128);be(0xf523,96);be(0xf53a,0xfe28);le(0xf53e,c.root-5)
 for tick=1,96 do
  if c.hit==1 and (tick==12 or tick==24) and p:read_u8(0xf520)~=0 and (p:read_u8(0xf52c)&1)==0 then
   p:write_u8(0xf40d,tick==12 and 1 or 255);cpu.state.IX.value=0xf520;call(0x321a)
  end
  if p:read_u8(0xf520)~=0 then cpu.state.IX.value=0xf520;call(0x2fe7) end
  emit(string.format('SHOT|%d|%d|%s|%d',id-1,tick,hex(0xf520,32),p:read_u8(0xfe28)))
 end
end
emit('COMPLETE');out:close();m:exit()
