-- Original ending presentation only; scheduler and actor-task deletion bypassed.
local m=manager.machine;local cpu=m.devices[':maincpu'];local dbg=m.debugger;local p=cpu.spaces.program
local out=assert(io.open('events.txt','w'));local tick=0;local enabled=false
local function hex(a,n)local t={} for i=0,n-1 do t[#t+1]=string.format('%02x',p:read_u8(a+i))end return table.concat(t)end
local function ret()local sp=cpu.state.SP.value;cpu.state.PC.value=p:read_u16(sp);cpu.state.SP.value=sp+2 end
local tap=p:install_write_tap(0xd080,0xd3bf,'ending_text',function(a,d,mask)
 if enabled then out:write(string.format('TEXT|%d|%d|%d\n',tick,a-0xd000,d))end
end)
assert(cpu.state.PC.value==0);dbg.visible_cpu=cpu
for a=0xd000,0xffff do p:write_u8(a,0)end
for a=0xd000,0xd3ff do p:write_u8(a,32)end
p:write_u8(0xf3a1,7);cpu.spaces.io:write_u8(1,6)
for _,start in ipairs({0x80b8,p:read_u16(0x8144)})do
 local ptr=start
 while p:read_u16(ptr)~=65535 do
  local src,dst,n=p:read_u16(ptr),p:read_u16(ptr+2),p:read_u16(ptr+4)
  for i=0,n-1 do p:write_u8(dst+i,p:read_u8(src+i))end
  ptr=ptr+6
 end
end
cpu.spaces.io:write_u8(0x0d,0);cpu.spaces.io:write_u8(6,0)
cpu.state.SP.value=0xe440;cpu.state.PC.value=0x7b98
for _,pc in ipairs({'0109','03d0','0116','7c6e','7ca9','2013'})do dbg:command('bp '..pc..':maincpu,1')end
enabled=true;local palette='';local scene=0
for guard=1,2000 do
 cpu.debug:go();repeat emu.wait_next_update()until dbg.execution_state=='stop'
 local pc=cpu.state.PC.value
 if pc==0x2013 then out:write('END|'..tick..'\n');break
 elseif pc==0x0109 then ret()
 elseif pc==0x03d0 then
  assert(cpu.state.DE.value>>8==2)
  out:write('CLEAR|'..tick..'\n');enabled=false
  for a=0xd080,0xd3bf do p:write_u8(a,32);p:write_u8(a+1024,0)end
  enabled=true;ret()
 elseif pc==0x7c6e then
  out:write('HIDE|'..tick..'\n');cpu.state.PC.value=0x7c70;cpu.state.AF.value=(6<<8)|(cpu.state.AF.value&255)
 elseif pc==0x7ca9 then
  scene=1;out:write(string.format('SCENE|%d|%s|%s\n',tick,hex(0xc000,512),hex(0xd800,2048)))
  dbg:command('bpclear');for _,at in ipairs({'0109','03d0','0116','2013'})do dbg:command('bp '..at..':maincpu,1')end
 elseif pc==0x0116 then
  local pal=hex(0xd860,96)..hex(0xdc60,96)
  if pal~=palette and scene==0 then out:write(string.format('PALETTE|%d|%s\n',tick,pal));palette=pal end
  local delay=(cpu.state.AF.value>>8)&255;out:write(string.format('WAIT|%d|%d\n',tick,delay));tick=tick+delay;ret()
 else error(string.format('unexpected %04x',pc))end
 assert(guard<2000)
end
enabled=false;out:write('COMPLETE\n');out:close();m:exit()
