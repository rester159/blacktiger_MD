local m=manager.machine;local cpu=m.devices[':maincpu'];local dbg=m.debugger
local p=cpu.spaces.program;local ports=cpu.spaces.io
local out=assert(io.open('events.txt','w'))
local function emit(s) out:write(s,'\n');out:flush() end
local function le(a,v) p:write_u8(a,v&255);p:write_u8(a+1,(v>>8)&255) end
local function be(a,v) p:write_u8(a,(v>>8)&255);p:write_u8(a+1,v&255) end
local function hex(a,n) local t={} for i=0,n-1 do t[#t+1]=string.format('%02x',p:read_u8(a+i)) end return table.concat(t) end
local function tile(g,x,y)
 if g==5 or g==6 then
  if x==400 and y>=320 and y<432 then return 1 end
 end
 if g==2 and x==416 and y>=384 then return 3 end
 if g==3 and x==416 and y>=400 then return 2 end
 if g==4 and y==352 then return 3 end
 if y>=432 and not (g==1 and x>=416) and not (g==6 and x==400) then return 3 end
 return 0
end
local data=dofile('cases.lua');assert(dbg and cpu.state.PC.value==0);dbg.visible_cpu=cpu
for id,c in ipairs(data.cases) do
 for a=0xe000,0xffff do p:write_u8(a,0) end
 for _,r in ipairs({'AF','BC','DE','HL','IX','IY'}) do cpu.state[r].value=0 end
 ports:write_u8(1,7);p:write_u8(0xe0e3,7);ports:write_u8(14,1);p:write_u8(0xe0e7,1)
 for bank=0,3 do
  ports:write_u8(13,bank)
  for at=0,4094,2 do
   local n=(bank*4096+at)//2
   local x=((n&15)|((n>>4)&0x70))*16;local y=(((n>>4)&15)|((n>>7)&0x30))*16
   local t=data.tiles[tile(c.geometry,x,y)+1]
   p:write_u8(0xc000+at,t&255);p:write_u8(0xc001+at,(t>>8)&7)
  end
 end
 be(0xe030,c.x-128);be(0xe032,c.y-144);be(0xf401,128);be(0xf403,144)
 p:write_u8(0xf400,128);p:write_u8(0xf419,c.ladder);p:write_u8(0xf418,c.falling);p:write_u8(0xe028,c.reversed);p:write_u8(0xf3ac,c.tier or 0)
 local history=0;local attacks=0
 for tick=1,c.ticks do
  local input=c.pattern[math.min(tick,#c.pattern)]
  history=((history<<1)|((input>>5)&1))&255
  p:write_u8(0xe0e8,input);p:write_u8(0xe903,history)
  attacks=((attacks<<1)|((input>>4)&1))&255;p:write_u8(0xe904,attacks)
  if c.hit and tick==c.hit then p:write_u8(0xf44a,1);p:write_u8(0xe906,1);p:write_u8(0xf447,10) end
  le(0xe160,0xe150);le(0xe140,0xe100)
  cpu.state.IX.value=0xf400;cpu.state.IY.value=0xe030;cpu.state.SP.value=0xeffe;cpu.state.PC.value=0x80c3
  dbg:command('bpclear');dbg:command('bp 81ef:maincpu,1');cpu.debug:go()
  repeat emu.wait_next_update() until dbg.execution_state=='stop'
  if c.attack then
   cpu.state.PC.value=0x83cc;dbg:command('bpclear');dbg:command('bp 85bc:maincpu,1');cpu.debug:go()
   repeat emu.wait_next_update() until dbg.execution_state=='stop'
  end
  emit(string.format('TICK|%d|%d|%s|%s|%s|%s',id-1,tick,hex(0xf400,40),hex(0xe030,4),hex(0xe901,20),hex(0xe054,1)))
  if c.attack then
   local slots={}
   for at=0xf440,0xf4e0,32 do slots[#slots+1]=hex(at,3)..hex(at+4,1)..hex(at+6,1) end
   emit(string.format('ATTACK|%d|%d|%s|%s|%s',id-1,tick,hex(0xf41a,8),hex(0xf447,5),table.concat(slots)))
  end
 end
end
emit('COMPLETE');out:close();m:exit()
