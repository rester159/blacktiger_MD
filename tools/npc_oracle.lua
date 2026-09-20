-- Development-only original-ROM oracle. No video is read or used.
local m=manager.machine
local cpu=m.devices[':maincpu'];local dbg=m.debugger
local p=cpu.spaces['program'];local ports=cpu.spaces['io']
local out=assert(io.open('events.txt','w'))
local function emit(s) out:write(s,'\n');out:flush() end
local function le(a,v) p:write_u8(a,v&255);p:write_u8(a+1,(v>>8)&255) end
local function be(a,v) p:write_u8(a,(v>>8)&255);p:write_u8(a+1,v&255) end
local function hex(a,n) local t={} for i=0,n-1 do t[#t+1]=string.format('%02x',p:read_u8(a+i)) end return table.concat(t) end
local function clean()
 for a=0xe000,0xffff do p:write_u8(a,0) end
 for _,r in ipairs({'AF','BC','DE','HL','IX','IY'}) do cpu.state[r].value=0 end
 ports:write_u8(1,0);p:write_u8(0xe0e3,0)
 le(0xe160,0xe150);p:write_u8(0xe010,1)
end
local function call(entry,finish)
 cpu.state['SP'].value=0xeffe;le(0xeffe,0x1e17);cpu.state['PC'].value=entry
 dbg:command('bpclear');dbg:command(string.format('bp %04x:maincpu,1',finish or 0x1e17))
 cpu.debug:go()
 repeat emu.wait_next_update() until dbg.execution_state=='stop'
 assert(cpu.state['PC'].value==(finish or 0x1e17))
end
assert(dbg and cpu.state['PC'].value==0);dbg.visible_cpu=cpu
for k=0,7 do
 clean();le(0xe923,128);le(0xe925,128);le(0xe927,0xec58)
 call(0x5e32+k*18)
 emit(string.format('NPC|%d|%s|%s',k,hex(0xf940,48),hex(0xec58,4)))
 if k==0 then
  for tick=1,402 do
   cpu.state['IX'].value=0xf940;call(0x32c7)
   if tick<=3 or tick>=199 then emit(string.format('IDLE|%d|%s|%s',tick,hex(0xf940,32),hex(0xfeac,16))) end
  end
 end
end
-- Shared 5-byte frame loader: hold-X must suppress BOTH velocity writes.
for _,entry in ipairs({0x2fe7,0x32c7}) do
 clean();local a=entry==0x2fe7 and 0xf520 or 0xf940;local display=entry==0x2fe7 and 0xfe28 or 0xfeac
 p:write_u8(a,0x80);be(a+1,80);be(a+3,80);p:write_u8(a+10,1);p:write_u8(a+12,3)
 be(a+26,display);le(a+30,0xe7fb)
 local data={2,0x20,0x45,1,2,3,0x22,0x4d,0x80,9,1,0x24,0x45,0xff,0x80,0xff,0x00,0xe8}
 for i,v in ipairs(data) do p:write_u8(0xe800+i-1,v) end
 for tick=1,14 do cpu.state['IX'].value=a;call(entry);emit(string.format('FRAME|%04x|%d|%s|%s',entry,tick,hex(a,32),hex(display,entry==0x2fe7 and 4 or 16))) end
end
clean();le(0xf3a7,123);call(0x5ff1,0x5ffb);emit('COINS|'..hex(0xf3a7,2))
clean();p:write_u8(0xf3b6,7);p:write_u8(0xf40e,1);p:write_u8(0xf421,2);call(0x6039,0x6043);emit('HEAL|'..hex(0xf40e,1)..'|'..hex(0xf421,1))
for sec=0,59 do
 clean();local bcd=(sec//10)*16+sec%10;le(0xf3b1,0x200+bcd);call(0x6064,0x6075)
 emit(string.format('TIME|%d|%s',sec,hex(0xf3b1,2)))
end
emit('COMPLETE');out:close();m:exit()
