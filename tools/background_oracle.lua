local m=manager.machine;local cpu=m.devices[':maincpu'];local dbg=m.debugger;local p=cpu.spaces.program
local out=assert(io.open('events.txt','w'));local id,tick,enabled=0,0,false
local tap=p:install_write_tap(0xc000,0xcfff,'background_capture',function(address,data,mask)
 if enabled then out:write(string.format('WRITE|%d|%d|%d|%d\n',id,tick,p:read_u8(0xe0e6)*4096+address-0xc000,data)) end
end)
assert(dbg and cpu.state.PC.value==0);dbg.visible_cpu=cpu
for n,c in ipairs(dofile('cases.lua')) do
 enabled=false;id=n-1;tick=0
 for a=0xe000,0xffff do p:write_u8(a,0) end
 p:write_u8(0xf3a1,c.round);p:write_u8(0xf3b7,c.alternate)
 cpu.state.PC.value=0x2a16;cpu.state.SP.value=0xe440
 dbg:command('bpclear');dbg:command('bp 0116:maincpu,1');enabled=true
 for step=1,24 do
  cpu.spaces.io:write_u8(6,0);cpu.debug:go();repeat emu.wait_next_update() until dbg.execution_state=='stop'
  assert(cpu.state.PC.value==0x0116)
  local delay=(cpu.state.AF.value>>8)&255
  out:write(string.format('WAIT|%d|%d|%d|%d\n',id,tick,p:read_u8(0xe043),delay));tick=tick+delay
  local sp=cpu.state.SP.value;cpu.state.PC.value=p:read_u8(sp)+256*p:read_u8(sp+1);cpu.state.SP.value=sp+2
 end
 out:flush()
end
enabled=false;out:write('COMPLETE\n');out:close();m:exit()
