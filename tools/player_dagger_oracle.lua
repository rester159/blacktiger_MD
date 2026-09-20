local m=manager.machine;local cpu=m.devices[':maincpu'];local dbg=m.debugger
local p=cpu.spaces.program;local ports=cpu.spaces.io
local out=assert(io.open('events.txt','w'))
local function emit(s)out:write(s,'\n');out:flush()end
local function le(a,v)p:write_u8(a,v&255);p:write_u8(a+1,(v>>8)&255)end
local function be(a,v)p:write_u8(a,(v>>8)&255);p:write_u8(a+1,v&255)end
local function hex(a,n)local t={} for i=0,n-1 do t[#t+1]=string.format('%02x',p:read_u8(a+i))end return table.concat(t)end
local function call(pc,stop)
 cpu.state.SP.value=0xeffe;cpu.state.PC.value=pc
 dbg:command('bpclear');dbg:command(string.format('bp %x:maincpu,1',stop));cpu.debug:go()
 repeat emu.wait_next_update() until dbg.execution_state=='stop'
end
local data=dofile('cases.lua');assert(cpu.state.PC.value==0);dbg.visible_cpu=cpu
for id,c in ipairs(data.cases)do
 for a=0xe000,0xffff do p:write_u8(a,0)end
 ports:write_u8(1,7);p:write_u8(0xe0e3,7);ports:write_u8(14,1);p:write_u8(0xe0e7,1)
 for bank=0,3 do
  ports:write_u8(13,bank)
  for at=0,4094,2 do
   local n=(bank*4096+at)//2;local x=((n&15)|((n>>4)&0x70))*16
   local tile=c.wall==1 and (x==416 or x==320) and data.solid or data.empty
   p:write_u8(0xc000+at,tile&255);p:write_u8(0xc001+at,(tile>>8)&7)
  end
 end
 be(0xe030,256);be(0xe032,256);le(0xe050,256);le(0xe052,256)
 be(0xf401,112);be(0xf403,96);p:write_u8(0xf426,c.low);p:write_u8(0xf41d,c.left*4)
 for volley=1,4 do p:write_u8(0xf421,1);call(0xa0b9,0xa19f)end
 emit(string.format('SPAWN|%d|%s',id-1,hex(0xfca0,288)))
 for tick=1,c.ticks do
  local old=256+(tick-1)*c.drift;local current=256+tick*c.drift
  le(0xe050,old);le(0xe052,256);be(0xe030,current);be(0xe032,256)
  if tick==c.hit then
   for at=0xfca0,0xfda0,32 do
    if p:read_u8(at)~=0 then p:write_u8(at,64);p:write_u8(at+10,1);le(at+30,0xa369)end
   end
  end
  call(0xa19f,0x2ece)
  emit(string.format('TICK|%d|%d|%s|%s',id-1,tick,hex(0xfca0,288),hex(0xfe00,36)))
 end
end
emit('COMPLETE');out:close();m:exit()
