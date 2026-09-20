local m=manager.machine;local cpu=m.devices[':maincpu'];local dbg=m.debugger;local p=cpu.spaces.program
local out=assert(io.open('events.txt','w'))
local function le(a,v)p:write_u8(a,v&255);p:write_u8(a+1,v>>8)end
local function hex(a,n)local t={} for i=0,n-1 do t[#t+1]=string.format('%02x',p:read_u8(a+i))end return table.concat(t)end
assert(cpu.state.PC.value==0);dbg.visible_cpu=cpu
for id,c in ipairs(dofile('cases.lua'))do
 for a=0xe000,0xffff do p:write_u8(a,0)end
 cpu.spaces.io:write_u8(6,0);p:write_u8(0xf3a1,c.round);p:write_u8(0xf3ac,c.weapon);p:write_u8(0xf3ad,c.armor)
 cpu.state.SP.value=0xe440;dbg:command('bpclear')
 if c.kind==0 then
  for i=0,3 do
   p:write_u8(0xffec+i*4,({3,2,11,10})[i+1]);p:write_u8(0xffed+i*4,8)
   p:write_u8(0xffee+i*4,144+(i//2)*16);p:write_u8(0xffef+i*4,112+(i%2)*16)
  end
  cpu.state.PC.value=0x5aac
  for _,pc in ipairs({'0116','5bab','5c0b','5c6e','7b98'})do dbg:command('bp '..pc..':maincpu,1')end
  local tick=0
  for guard=1,100 do
   cpu.spaces.io:write_u8(6,0);cpu.debug:go();repeat emu.wait_next_update()until dbg.execution_state=='stop'
   local pc=cpu.state.PC.value
   if pc==0x5c6e or pc==0x7b98 then out:write(string.format('END|%d|%d|%d\n',id-1,tick,pc));break
   elseif pc==0x5bab then cpu.state.PC.value=0x5bbf -- protection-only read loop, before stack pushes
   elseif pc==0x5c0b then cpu.state.PC.value=0x5c1d -- protection-only checksum, before stack pushes
   else
    assert(pc==0x0116);local delay=(cpu.state.AF.value>>8)&255
    out:write(string.format('FRAME|%d|%d|%d|%d|%s|%s\n',id-1,tick,delay,p:read_u8(0xf3ad),hex(0xffec,16),hex(0xffd4,8)))
    tick=tick+delay;local sp=cpu.state.SP.value;cpu.state.PC.value=p:read_u8(sp)+256*p:read_u8(sp+1);cpu.state.SP.value=sp+2
   end
   assert(guard<100)
  end
 else
  le(0xf3a7,c.coins);local v=c.coins;for a=0xf3a6,0xf3a2,-1 do p:write_u8(a,v%10);v=v//10 end
  cpu.state.PC.value=0x5ccc;dbg:command('bp 5cef:maincpu,1');cpu.debug:go();repeat emu.wait_next_update()until dbg.execution_state=='stop'
  out:write(string.format('REWARD|%d|%d|%s\n',id-1,p:read_u16(0xf3a7),hex(0xf3a2,5)))
 end
 out:flush()
end
out:write('COMPLETE\n');out:close();m:exit()
