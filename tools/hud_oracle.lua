-- Original start sequence observation; development only.
local m=manager.machine;local cpu=m.devices[':maincpu'];local p=cpu.spaces.program
local out=assert(io.open('events.txt','w'));local bank=0;local recording=false
local tap=cpu.spaces.io:install_write_tap(0x0d,0x0d,'bank',function(a,d)if not recording then bank=d end end)
local scroll={0,0,0,0};local st=cpu.spaces.io:install_write_tap(8,11,'scroll',function(a,d)scroll[a-7]=d end)
local sound=cpu.spaces.io:install_write_tap(0,0,'sound',function(a,d)out:write(string.format('SOUND|%d|%d\n',tick or 0,d))end)
local function bghex()local t={} for i=0,511 do t[#t+1]=string.format('%02x',m.memory.shares[':scrollram']:read_u8(i))end return table.concat(t)end
local function hex(a,n)local t={} for i=0,n-1 do t[#t+1]=string.format('%02x',p:read_u8(a+i))end return table.concat(t)end
cpu.debug:go()
for frame=1,1800 do
 emu.wait_next_update()
 if frame==600 then m.ioport.ports[':IN0'].fields['Coin 1']:set_value(1) end
 if frame==606 then m.ioport.ports[':IN0'].fields['Coin 1']:set_value(0) end
 if frame==650 then m.ioport.ports[':IN0'].fields['1 Player Start']:set_value(1) end
 if frame==656 then m.ioport.ports[':IN0'].fields['1 Player Start']:set_value(0) end
end
m.screens[':screen']:snapshot('hud.png')
out:write('HUD|'..hex(0xd000,2048)..'|'..hex(0xd800,2048)..'|'..hex(0xfe00,512)..'\nCOMPLETE\n');out:close();m:exit()
