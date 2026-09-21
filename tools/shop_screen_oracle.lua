-- Development-only observation of original shop presentation.
local m=manager.machine;local cpu=m.devices[':maincpu'];local dbg=m.debugger;local p=cpu.spaces.program
local out=assert(io.open('events.txt','w'))
local function hex(a,n)local t={} for i=0,n-1 do t[#t+1]=string.format('%02x',p:read_u8(a+i))end return table.concat(t)end
local function ret()local sp=cpu.state.SP.value;cpu.state.PC.value=p:read_u16(sp);cpu.state.SP.value=sp+2 end
cpu.debug:go()
for frame=1,1800 do
 emu.wait_next_update()
 if frame==600 then m.ioport.ports[':IN0'].fields['Coin 1']:set_value(1) end
 if frame==606 then m.ioport.ports[':IN0'].fields['Coin 1']:set_value(0) end
 if frame==650 then m.ioport.ports[':IN0'].fields['1 Player Start']:set_value(1) end
 if frame==656 then m.ioport.ports[':IN0'].fields['1 Player Start']:set_value(0) end
end
dbg:command('bp 0038:maincpu,1');repeat emu.wait_next_update()until dbg.execution_state=='stop'
cpu.state.SP.value=0xeff0;cpu.state.PC.value=0x63a7
p:write_u16(0xf3a7,12345)
dbg:command('bpclear')
for _,pc in ipairs({'0109','00f6','0116','0300','192b'})do dbg:command('bp '..pc..':maincpu,1')end
for guard=1,180 do
 cpu.debug:go();repeat emu.wait_next_update()until dbg.execution_state=='stop'
 local pc=cpu.state.PC.value
 out:write(string.format('STOP|%04x\n',pc));out:flush()
 if pc==0x192b then break end
 ret()
 if guard==180 then
 out:write('SHOP|'..hex(0xc000,512)..'|'..hex(0xd000,2048)..'|'..hex(0xd800,2048)..'|'..hex(0xfe00,512)..'\n')
 m.screens[':screen']:snapshot('shop.png')
 end
end
out:write('COMPLETE\n');out:close();m:exit()
