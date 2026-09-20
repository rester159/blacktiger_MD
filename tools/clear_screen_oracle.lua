-- Development-only execution of original bonus-screen setup; no code enters ROM.
local m=manager.machine;local cpu=m.devices[':maincpu'];local dbg=m.debugger;local p=cpu.spaces.program
local out=assert(io.open('events.txt','w'))
local function hex(a,n)local t={} for i=0,n-1 do t[#t+1]=string.format('%02x',p:read_u8(a+i))end return table.concat(t)end
local function ret()local sp=cpu.state.SP.value;cpu.state.PC.value=p:read_u16(sp);cpu.state.SP.value=sp+2 end
assert(cpu.state.PC.value==0);dbg.visible_cpu=cpu
for r=0,6 do
 for a=0xd000,0xffff do p:write_u8(a,0)end
 for a=0xd000,0xd3ff do p:write_u8(a,0x20)end
 p:write_u8(0xf3a1,r);p:write_u16(0xe140,0xe100)
 -- Round palette already exists at clear entry. Load its source data lists.
 cpu.spaces.io:write_u8(1,6)
 for _,start in ipairs({0x80b8,p:read_u16(0x8136+r*2)})do
 local ptr=start
 while p:read_u16(ptr)~=65535 do
  local src,dst,n=p:read_u16(ptr),p:read_u16(ptr+2),p:read_u16(ptr+4)
  for i=0,n-1 do p:write_u8(dst+i,p:read_u8(src+i))end
  ptr=ptr+6
 end
 end
 cpu.spaces.io:write_u8(0x0d,0);cpu.spaces.io:write_u8(6,0)
 cpu.state.SP.value=0xe440;cpu.state.PC.value=0x5c82
 dbg:command('bpclear');dbg:command('bp 0300:maincpu,1');dbg:command('bp 5cef:maincpu,1')
 for guard=1,10 do
  cpu.debug:go();repeat emu.wait_next_update()until dbg.execution_state=='stop'
  if cpu.state.PC.value==0x5cef then break end
  assert(cpu.state.PC.value==0x0300 and guard<10);ret()
 end
 assert(cpu.state.PC.value==0x5cef)
 -- Consume the queued source string through its original handler.
 p:write_u8(0xe144,p:read_u8(0xe101));cpu.state.SP.value=0xe440;p:write_u16(0xe440,0x0100)
 cpu.state.PC.value=0x1429;dbg:command('bpclear');dbg:command('bp 0100:maincpu,1')
 cpu.debug:go();repeat emu.wait_next_update()until dbg.execution_state=='stop'
 assert(cpu.state.PC.value==0x0100)
 out:write(string.format('SCREEN|%d|%s|%s|%s\n',r,hex(0xc000,512),hex(0xd000,2048),hex(0xd800,2048)))
end
out:write('COMPLETE\n');out:close();m:exit()
