local m=manager.machine;local cpu=m.devices[':maincpu'];local dbg=m.debugger
local p=cpu.spaces.program;local ports=cpu.spaces.io
local out=assert(io.open('events.txt','w'))
local function emit(s) out:write(s,'\n');out:flush() end
local function le(a,v) p:write_u8(a,v&255);p:write_u8(a+1,(v>>8)&255) end
local function be(a,v) p:write_u8(a,(v>>8)&255);p:write_u8(a+1,v&255) end
local function hex(a,n) local t={} for i=0,n-1 do t[#t+1]=string.format('%02x',p:read_u8(a+i)) end return table.concat(t) end
local function clean(category,sample)
 for a=0xe000,0xffff do p:write_u8(a,0) end
 for _,r in ipairs({'AF','BC','DE','HL','IX','IY'}) do cpu.state[r].value=0 end
 ports:write_u8(1,0);p:write_u8(0xe0e3,0);p:write_u8(0xe010,1)
 le(0xe160,0xe150);le(0xe140,0xe100)
 cpu.state.IX.value=0xf940;p:write_u8(0xf94b,category);be(0xf941,80);be(0xf943,80);p:write_u8(0xe009,sample)
 le(0xf3a7,123)
end
local function call(pc,finish)
 cpu.state.SP.value=0xeffe;le(0xeffe,0x1e17);cpu.state.PC.value=pc
 dbg:command('bpclear');dbg:command(string.format('bp %04x:maincpu,1',finish or 0x1e17));cpu.debug:go()
 repeat emu.wait_next_update() until dbg.execution_state=='stop'
 assert(cpu.state.PC.value==(finish or 0x1e17))
end
assert(dbg and cpu.state.PC.value==0);dbg.visible_cpu=cpu
for kind,pc in ipairs({0xb4af,0xb515}) do
 clean(0,0);ports:write_u8(1,4);p:write_u8(0xe0e3,4)
 le(0xe923,128);le(0xe925,96);le(0xe927,0xec58)
 call(pc);cpu.state.IX.value=0xf520
 le(0xf3b1,0x0120)
 for tick=1,203 do
  if p:read_u8(0xf520)~=0 then call(0x2fe7) end
  if tick==202 then call(0x4744) end
  emit(string.format('ITEM|%d|%d|%s|%s|%s|%s',kind,tick,hex(0xf520,32),hex(0xfe28,4),hex(0xf3b1,2),hex(0xec58,1)))
 end
end
for _,size in ipairs({32,48,96}) do for contact=0,63 do
 clean(0,0);ports:write_u8(1,4);p:write_u8(0xe0e3,4)
 -- Calling the screen effect on a separate safe item isolates one target record.
 cpu.state.IX.value=0xf520;p:write_u8(0xf520,0x80);p:write_u8(0xf52d,25);le(0xf538,0xec58)
 local at=size==32 and 0xf540 or size==48 and 0xf940 or 0xfc10
 p:write_u8(at,0x80);p:write_u8(at+13,contact);p:write_u8(at+14,100);p:write_u8(at+21,100)
 call(0xb57b)
 emit(string.format('TARGET|%d|%d|%d',size,contact,p:read_u8(at)))
end end
emit('COMPLETE');out:close();m:exit()
