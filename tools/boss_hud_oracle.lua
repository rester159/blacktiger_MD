-- Execute original boss HUD routines with controlled layer counts.
local m=manager.machine;local cpu=m.devices[':maincpu'];local dbg=m.debugger;local p=cpu.spaces.program
local out=assert(io.open('events.txt','w'))
local function hex(a,n)local t={}for i=0,n-1 do t[#t+1]=string.format('%02x',p:read_u8(a+i))end return table.concat(t)end
local function call(pc)
 cpu.state.SP.value=0xeffe;p:write_u16(0xeffe,0x1e17);cpu.state.PC.value=pc
 dbg:command('bpclear');dbg:command('bp 1e17:maincpu,1');cpu.debug:go();repeat emu.wait_next_update()until dbg.execution_state=='stop'
 assert(cpu.state.PC.value==0x1e17)
end
for level=0,7 do
 local count=p:read_u8(0x5db6+level*2);local attr=p:read_u8(0x5db7+level*2)
 p:write_u8(0xf3a1,level);cpu.state.IX.value=0xf940
 for life=count,0,-1 do
  for i=0,1023 do p:write_u8(0xd000+i,0x20);p:write_u8(0xd400+i,0)end
  p:write_u8(0xf955,life);call(0x5d6d)
  out:write(string.format('ROW|%d|%d|%d|%d|%s|%s\n',level,life,count,attr,hex(0xd0c0,32),hex(0xd4c0,32)))
 end
end
out:write('COMPLETE\n');out:close();m:exit()
