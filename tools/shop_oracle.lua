local m=manager.machine;local cpu=m.devices[':maincpu'];local dbg=m.debugger
local p=cpu.spaces.program;local out=assert(io.open('events.txt','w'))
local function le(a,v) p:write_u8(a,v&255);p:write_u8(a+1,(v>>8)&255) end
assert(dbg and cpu.state.PC.value==0);dbg.visible_cpu=cpu
out:write(string.format('CONFIG|%d\n',((~cpu.spaces.io:read_u8(4))&28)>>2))
for id,c in ipairs(dofile('cases.lua')) do
 for a=0xe000,0xffff do p:write_u8(a,0) end
 le(0xe160,0xe150);p:write_u8(0xe010,1)
 le(0xf3a7,c.coins);p:write_u8(0xe022,c.difficulty);p:write_u8(0xf3ac,c.weapon);p:write_u8(0xf3ad,c.armor)
 p:write_u8(0xf3ab,c.keys);p:write_u8(0xf3b0,c.antidotes);p:write_u8(0xe915,c.poison);p:write_u8(0xf421,1)
 cpu.state.PC.value=c.pc;cpu.state.SP.value=0xeffe
 while true do
  dbg:command('bpclear')
  for _,pc in ipairs({'67eb','67fe','6946','25f3','0109'}) do dbg:command('bp '..pc..':maincpu,1') end
  cpu.debug:go();repeat emu.wait_next_update() until dbg.execution_state=='stop'
  local pc=cpu.state.PC.value
  if pc==0x67eb or pc==0x67fe then break end
  -- Bypass presentation/task setup; the economic writes execute unmodified.
  local sp=cpu.state.SP.value;cpu.state.PC.value=p:read_u16(sp);cpu.state.SP.value=sp+2
 end
 out:write(string.format('BUY|%d|%d|%d|%d|%d|%d|%d|%d|%d\n',id-1,cpu.state.PC.value==0x67eb and 1 or 0,p:read_u16(0xf3a7),p:read_u8(0xf3ac),p:read_u8(0xf3ad),p:read_u8(0xf3ab),p:read_u8(0xf3b0),p:read_u8(0xe915),p:read_u8(0xf421)))
 local sounds={}
 for a=0xe150,p:read_u16(0xe160)-1 do sounds[#sounds+1]=string.format('%02x',p:read_u8(a)) end
 out:write(string.format('SOUND|%d|%s\n',id-1,table.concat(sounds)))
end
out:write('COMPLETE\n');out:close();m:exit()
