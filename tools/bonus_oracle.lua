local m=manager.machine;local cpu=m.devices[':maincpu'];local dbg=m.debugger;local p=cpu.spaces.program
local out=assert(io.open('events.txt','w'))
local function le(a,v) p:write_u8(a,v&255);p:write_u8(a+1,(v>>8)&255) end
local function be(a,v) p:write_u8(a,(v>>8)&255);p:write_u8(a+1,v&255) end
local function word(a) return p:read_u8(a)*256+p:read_u8(a+1) end
assert(dbg and cpu.state.PC.value==0);dbg.visible_cpu=cpu
for id,c in ipairs(dofile('cases.lua')) do
 cpu.spaces.io:write_u8(6,0)
 for a=0xe000,0xffff do p:write_u8(a,0) end
 cpu.state.SP.value=0xeffe;le(0xeffe,0xe100);cpu.state.IX.value=0xf520
 dbg:command('bpclear')
 if c.kind==0 then
  p:write_u8(0xf412,c.jumping);p:write_u8(0xf418,c.falling);p:write_u8(0xf416,c.returning)
  p:write_u8(0xf41a,1);le(0xf538,0xeaa0);p:write_u8(0xeaa0,c.flags)
  cpu.state.PC.value=0x4f8c;dbg:command('bp 6fd7:maincpu,1');dbg:command('bp e100:maincpu,1');cpu.debug:go()
  repeat emu.wait_next_update() until dbg.execution_state=='stop'
  out:write(string.format('CONTACT|%d|%d|%d|%d|%d\n',id-1,cpu.state.PC.value==0x6fd7 and 1 or 0,p:read_u8(0xeaa0),p:read_u8(0xf41a),p:read_u8(0xf52c)))
 else
  p:write_u8(0xf3a1,c.round);p:write_u8(0xf3b7,c.alternate);be(0xe030,c.x);be(0xe032,c.y);be(0xe038,c.saved_x);be(0xe03a,c.saved_y)
  cpu.state.PC.value=0x7030
  for _,pc in ipairs({'7073','7076','707b','708c','7094','7097'}) do dbg:command('bp '..pc..':maincpu,1') end
  local music=0
  while true do
   if cpu.state.PC.value==0x7097 then break end
   cpu.spaces.io:write_u8(6,0);cpu.debug:go();repeat emu.wait_next_update() until dbg.execution_state=='stop'
   local pc=cpu.state.PC.value
   if pc==0x7097 then break end
   if pc==0x707b or pc==0x7094 then music=(cpu.state.AF.value>>8)&255 end
   cpu.state.PC.value=pc+3 -- Skip scheduling/audio only; run camera instructions unchanged.
  end
  out:write(string.format('CAMERA|%d|%d|%d|%d|%d|%d|%d\n',id-1,word(0xe030),word(0xe032),word(0xe038),word(0xe03a),p:read_u8(0xf3b7),music))
 end
 out:flush()
end
out:write('COMPLETE\n');out:close();m:exit()
