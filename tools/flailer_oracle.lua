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
 ports:write_u8(1,0);p:write_u8(0xe0e3,0);ports:write_u8(14,1);p:write_u8(0xe0e7,1)
 le(0xe160,0xe150);le(0xe140,0xe100);p:write_u8(0xe010,1);p:write_u8(0xe022,4)
 for bank=0,3 do
  ports:write_u8(13,bank)
  for at=0,4094,2 do
   local n=(bank*4096+at)//2
   local x=((n&15)|((n>>4)&0x70))*16;local y=(((n>>4)&15)|((n>>7)&0x30))*16
   local tile=data.empty
   if y>=128 or (c.wall>0 and x>=160 and x<176 and y>=c.wall) then tile=data.solid end
   p:write_u8(0xc000+at,tile&255);p:write_u8(0xc001+at,(tile>>8)&7)
  end
 end
 le(0xe923,128);le(0xe925,c.y);le(0xe927,0xec58);be(0xf401,c.px);be(0xf403,c.py);p:write_u8(0xf41d,c.face*4)
 for i=0,47 do p:write_u8(0xf940+i,p:read_u8(c.template+i)) end
 be(0xf941,128);be(0xf943,c.y);le(0xf958,0xec58);be(0xf95a,0xfeac)
 p:write_u8(0xec58,1);cpu.state.IX.value=0xf940
 le(0xf95e,c.root-5);p:write_u8(0xf94a,1);p:write_u8(0xf947,c.vy&255)
 p:write_u8(0xe009,c.random)
 local finished=false
 for tick=1,c.ticks do
  if c.damage>0 and tick>=80 and tick%80==0 and p:read_u8(0xf940)==0x80 and (p:read_u8(0xf94c)&1)==0 then p:write_u8(0xf40d,c.damage);cpu.state.IX.value=0xf940;call(0x321a) end
  for at=0xf520,0xf920,32 do p:write_u8(at,0) end
  if not finished and p:read_u8(0xf940)~=0 then cpu.state.IX.value=0xf940;finished=not call(0x32c7) end
  local reward=false;for at=0xe100,0xe13e,2 do if p:read_u8(at)==5 and p:read_u8(at+1)==c.score then reward=true end end
  emit(string.format('TICK|%d|%d|%s|%s|%s|%s|%s',id-1,tick,hex(0xf940,48),hex(0xfeac,16),finished and '1' or '0',hex(0xec58,1),reward and 'REWARD' or '0000'))
 end
end
emit('COMPLETE');out:close();m:exit()
