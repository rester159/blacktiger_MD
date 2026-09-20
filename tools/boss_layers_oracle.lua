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
for id,c in ipairs(cases) do
 clean(0,0);ports:write_u8(1,4);p:write_u8(0xe0e3,4)
 for i=0,47 do p:write_u8(0xf940+i,p:read_u8(c.template+i)) end
 cpu.state.IX.value=0xf940;le(0xf958,0xec58);be(0xf95a,0xfeac)
 for hit,damage in ipairs(c.damage) do
  p:write_u8(0xf40d,damage);call(0x321a)
  if p:read_u8(0xf940)==0x40 then call(0xa0b0) end
  emit(string.format('HIT|%d|%d|%d|%d|%d|%d',id-1,hit,p:read_u8(0xf94e),p:read_u8(0xf955),p:read_u8(0xf940),p:read_u8(0xe02f)))
 end
end
emit('COMPLETE');out:close();m:exit()
