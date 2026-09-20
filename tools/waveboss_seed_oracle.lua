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
 ports:write_u8(1,1);p:write_u8(0xe0e3,1);ports:write_u8(14,1);p:write_u8(0xe0e7,1)
 le(0xe160,0xe150);le(0xe140,0xe100);p:write_u8(0xe010,1);p:write_u8(0xe022,4)
 for bank=0,3 do
  ports:write_u8(13,bank)
  for at=0,4094,2 do
   local n=(bank*4096+at)//2
   local x=((n&15)|((n>>4)&0x70))*16;local y=(((n>>4)&15)|((n>>7)&0x30))*16
   local tile=data.empty
   if y>=160 or (c.wall>0 and x>=160 and x<176 and y>=c.wall) then tile=data.solid end
   p:write_u8(0xc000+at,tile&255);p:write_u8(0xc001+at,(tile>>8)&7)
  end
 end
 le(0xe923,128);le(0xe925,c.y);le(0xe927,0xec58);be(0xf401,c.px);be(0xf403,c.py);p:write_u8(0xf41d,0)
 for i=0,31 do p:write_u8(0xf520+i,p:read_u8(c.template+i)) end
 be(0xf521,128);be(0xf523,c.y);le(0xf538,0xec58);be(0xf53a,0xfe28)
 p:write_u8(0xec58,2);cpu.state.IX.value=0xf520
 le(0xf53e,c.root-5);p:write_u8(0xf52a,1);p:write_u8(0xf527,0)
 p:write_u8(0xf534,c.left);p:write_u8(0xf530,31+c.profile)
 local finished=false
 for tick=1,c.ticks do
  if false and c.hit_tick==tick and p:read_u8(0xf520)==0x80 then p:write_u8(0xf40d,c.damage);cpu.state.IX.value=0xf520;call(0x321a) end
  if false and c.hit2_tick==tick and p:read_u8(0xf520)==0x80 then p:write_u8(0xf40d,c.damage2);cpu.state.IX.value=0xf520;call(0x321a) end
  if not finished and p:read_u8(0xf520)~=0 then cpu.state.IX.value=0xf520;finished=not call(0x2fe7) end
  emit(string.format('TICK|%d|%d|%s|%s|%s|%s|%s',id-1,tick,hex(0xf520,32),hex(0xfe28,16),finished and '1' or '0',hex(0xec58,1),hex(0xe100,2)))
 end
end
emit('COMPLETE');out:close();m:exit()
