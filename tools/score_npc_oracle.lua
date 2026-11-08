-- Original display and NPC contact routines, isolated from board scheduling.
local m=manager.machine;local cpu=m.devices[':maincpu'];local dbg=m.debugger;local p=cpu.spaces.program
local out=assert(io.open('events.txt','w'))
local function le(a,v)p:write_u8(a,v&255);p:write_u8(a+1,v>>8)end
local function call(pc)
 cpu.state.SP.value=0xeffe;le(0xeffe,0x1e17);cpu.state.PC.value=pc
 dbg:command('bpclear');dbg:command('bp 1e17:maincpu,1');cpu.debug:go()
 repeat emu.wait_next_update()until dbg.execution_state=='stop'
 assert(cpu.state.PC.value==0x1e17)
end
assert(cpu.state.PC.value==0);dbg.visible_cpu=cpu
for mask=0,7 do
 for a=0xe000,0xffff do p:write_u8(a,0)end
 p:write_u8(0xf412,mask&1);p:write_u8(0xf416,(mask>>1)&1);p:write_u8(0xf418,(mask>>2)&1)
 le(0xe160,0xe150);cpu.state.IX.value=0xf940
 p:write_u8(0xf95c,0x5f);p:write_u8(0xf95d,0x67)
 call(0x4995)
 out:write(string.format('CONTACT|%d|%d\n',mask,p:read_u8(0xf94a)))
end
for _,value in ipairs({0,1,100,20000,54321,8765432,99999999})do
 local digits=string.format('%08d',value)
 for i=0,8 do p:write_u8(0xd060+i,32)end
 for i=1,8 do p:write_u8(0xe1e7+i,tonumber(digits:sub(i,i)))end
 cpu.state.HL.value=0xd060;cpu.state.DE.value=0xe1e8;call(0x054f)
 local chars={}
 for i=0,8 do local c=p:read_u8(0xd060+i);chars[#chars+1]=c==32 and ' ' or tostring(c)end
 out:write(string.format('SCORE|%d|%s\n',value,table.concat(chars)))
end
out:write('COMPLETE\n');out:close();m:exit()
