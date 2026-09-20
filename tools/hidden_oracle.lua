local m=manager.machine;local cpu=m.devices[':maincpu'];local dbg=m.debugger
local p=cpu.spaces.program;local ports=cpu.spaces.io
local out=assert(io.open('events.txt','w'))
local function emit(s) out:write(s,'\n');out:flush() end
local function le(a,v) p:write_u8(a,v&255);p:write_u8(a+1,(v>>8)&255) end
local function hex(a,n) local t={} for i=0,n-1 do t[#t+1]=string.format('%02x',p:read_u8(a+i)) end return table.concat(t) end
local function clean(r,k)
 for a=0xe000,0xffff do p:write_u8(a,0) end
 for _,reg in ipairs({'AF','BC','DE','HL','IX','IY'}) do cpu.state[reg].value=0 end
 ports:write_u8(1,2);p:write_u8(0xe0e3,2)
 le(0xe160,0xe150);le(0xe140,0xe100);p:write_u8(0xe010,1);p:write_u8(0xe022,4)
 le(0xe923,128);le(0xe925,128);le(0xe927,0xec58);p:write_u8(0xe930,k)
 p:write_u8(0xf3a1,r);p:write_u8(0xf3a0,3);p:write_u8(0xf3ad,2);p:write_u8(0xf3b6,4);p:write_u8(0xf40e,1)
 le(0xf3a7,123);le(0xf3b1,0x200);p:write_u8(0xf40d,5)
end
local function call(pc,finish)
 cpu.state.SP.value=0xeffe;le(0xeffe,0x1e17);cpu.state.PC.value=pc
 dbg:command('bpclear');dbg:command(string.format('bp %04x:maincpu,1',finish or 0x1e17));cpu.debug:go()
 repeat emu.wait_next_update() until dbg.execution_state=='stop'
 assert(cpu.state.PC.value==(finish or 0x1e17))
end
local cases=dofile('cases.lua');assert(dbg and cpu.state.PC.value==0);dbg.visible_cpu=cpu
for _,c in ipairs(cases) do
 clean(c.round,c.persistent);ports:write_u8(0x0d,c.bank)
 for _,delta in ipairs({0,1,32,33}) do p:write_u8(c.address+delta,0xa5) end
 call(0xb7da);cpu.state.IX.value=0xf520;call(0x2fe7)
 call(0x321a);call(0x2fe7)
 ports:write_u8(0x0d,c.bank)
 emit(string.format('PATCH|%d|%d|%s|%s|%s',c.round,c.persistent,hex(c.address,2),hex(c.address+32,2),hex(0xec58,1)))
end
for k=0,11 do
 clean(0,41);call(0xb7da+23*k);cpu.state.IX.value=0xf520;call(0x2fe7);call(0x321a);call(0x2fe7)
 for tick=1,3 do call(0x2fe7) end
 emit(string.format('REVEAL|%d|%s|%s',k,hex(0xf520,32),hex(0xfe28,4)))
 call(0x4744)
 emit(string.format('REWARD|%d|%s|%s|%s|%s|%s|%s|%s',k,hex(0xf3a0,1),hex(0xf3ad,1),hex(0xf40e,1),hex(0xf3a7,2),hex(0xf3b1,2),hex(0xe100,4),hex(0xf520,32)))
end
emit('COMPLETE');out:close();m:exit()
