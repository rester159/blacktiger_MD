-- Original ROM idle/credit presentation capture; development only.
local m=manager.machine;local cpu=m.devices[':maincpu'];local p=cpu.spaces.program
local out=assert(io.open('full.bin','wb'));local meta=assert(io.open('full.tsv','w'));local scroll={0,0,0,0};local ctrl=0;local enable=0;local layout=1
local taps={}
taps[1]=cpu.spaces.io:install_write_tap(8,11,'scroll',function(a,d)scroll[a-7]=d end)
taps[2]=cpu.spaces.io:install_write_tap(4,4,'ctrl',function(a,d)ctrl=d end)
taps[3]=cpu.spaces.io:install_write_tap(12,12,'enable',function(a,d)enable=d end)
taps[4]=cpu.spaces.io:install_write_tap(14,14,'layout',function(a,d)layout=d end)
local function bytes(a,n)local t={} for i=0,n-1 do t[#t+1]=string.char(p:read_u8(a+i))end return table.concat(t)end
cpu.debug:go()
for frame=1,5100 do
 emu.wait_next_update()
 if frame==4801 then m.ioport.ports[':IN0'].fields['Coin 1']:set_value(1)end
 if frame==4807 then m.ioport.ports[':IN0'].fields['Coin 1']:set_value(0)end
 local sx=scroll[1]+scroll[2]*256;local sy=scroll[3]+scroll[4]*256
 local bg={};local ram=m.memory.shares[':scrollram']
 for y=0,14 do for x=0,16 do
  local col=((sx//16)+x)&127;local row=((sy+16)//16+y)&127
  local at
  if layout==1 then at=((col&15)+((row&15)<<4)+((col&112)<<4)+((row&48)<<7))*2
  else at=((col&15)+((row&15)<<4)+((col&48)<<4)+((row&112)<<6))*2 end
  bg[#bg+1]=string.char(ram:read_u8(at),ram:read_u8(at+1))
 end end
 out:write(string.char(sx&255,(sx>>8)&255,sy&255,(sy>>8)&255,ctrl,enable,layout,p:read_u8(0xe080)),table.concat(bg),bytes(0xd000,2048),bytes(0xd800,2048),bytes(0xfe00,512))
 meta:write(string.format('%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n',frame,p:read_u8(0xe080),p:read_u16(0xe016),p:read_u8(0xe018),sx,sy,ctrl,enable,p:read_u8(0xf400)))
 if frame%300==0 then m.screens[':screen']:snapshot(string.format('full-%05d.png',frame))end
end
out:close();meta:close();local done=assert(io.open('events.txt','w'));done:write('FRAMES|5100\nCOMPLETE\n');done:close();m:exit()
