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
local cases=dofile('cases.lua')
for category=0,27 do for sample=0,31 do
 clean(category,sample);call(0x54e9)
 emit(string.format('DROP|%d|%d|%s',category,sample,hex(0xf520,32)))
end end
for kind,c in ipairs(cases) do
 clean(c.category,c.sample);call(0x54e9);cpu.state.IX.value=0xf520
 for tick=1,241 do
  if p:read_u8(0xf520)~=0 then call(0x2fe7) end
  emit(string.format('FRAME|%d|%d|%s|%s',kind,tick,hex(0xf520,32),hex(0xfe28,4)))
 end
 clean(c.category,c.sample);call(0x54e9);cpu.state.IX.value=0xf520;call(0x2fe7);call(0x4744)
 emit(string.format('COINS|%d|%s|%s',kind,hex(0xf3a7,2),hex(0xf520,32)))
end
clean(1,0)
for a=0xf520,0xf920,32 do p:write_u8(a,0x80) end
call(0x54e9);emit('FULL|'..hex(0xf520,32)..'|'..hex(0xf940,32))
for _,seed in ipairs({0,1,255,256,451,32767,65535}) do
 clean(0,0);le(0xe008,seed)
 for tick=1,64 do call(0x9b9,0x9c6);emit(string.format('RNG|%d|%d|%s',seed,tick,hex(0xe008,2))) end
end
emit('COMPLETE');out:close();m:exit()
