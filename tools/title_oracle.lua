-- Development-only original title capture. No source code enters the cartridge.
local m=manager.machine;local cpu=m.devices[':maincpu'];local p=cpu.spaces.program
local out=assert(io.open('events.txt','w'))
local function hex(a,n)local t={} for i=0,n-1 do t[#t+1]=string.format('%02x',p:read_u8(a+i))end return table.concat(t)end
cpu.debug:go()
for frame=1,1800 do
 emu.wait_next_update()
 if frame%120==0 then
  m.screens[':screen']:snapshot(string.format('title-%04d.png',frame))
  out:write(string.format('SCREEN|%d|%s|%s|%s\n',frame,hex(0xc000,4096),hex(0xd000,2048),hex(0xd800,2048)))
 end
end
out:write('COMPLETE\n');out:close();m:exit()
