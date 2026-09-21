-- Task-relative rescue sequence. Original dialogue and reward code executes;
-- scheduler/task-list helpers and reward HUD refresh are bypassed explicitly.
local m=manager.machine;local cpu=m.devices[':maincpu'];local dbg=m.debugger;local p=cpu.spaces.program
local out=assert(io.open('events.txt','w'));local tick=0;local kind=0;local enabled=false
local function emit(tag,a,b)out:write(string.format('%s|%d|%d|%d|%d\n',tag,kind,tick,a or 0,b or 0))end
local function le(a,v)p:write_u8(a,v&255);p:write_u8(a+1,v>>8)end
local function ret()local sp=cpu.state.SP.value;cpu.state.PC.value=p:read_u16(sp);cpu.state.SP.value=sp+2 end
local tap=p:install_write_tap(0xd100,0xd17f,'npc_text',function(a,d,mask)if enabled then emit('TEXT',a-0xd000,d)end end)
local attrtap=p:install_write_tap(0xd500,0xd57f,'npc_attr',function(a,d,mask)if enabled then emit('ATTR',a-0xd400,d)end end)
local soundtap=p:install_write_tap(0xe150,0xe15f,'npc_sound',function(a,d,mask)if enabled then emit('SOUND',d)end end)
assert(cpu.state.PC.value==0);dbg.visible_cpu=cpu
for k=1,8 do
 kind=k;tick=0;enabled=false
 for a=0xe000,0xffff do p:write_u8(a,0)end
 for a=0xd000,0xd3ff do p:write_u8(a,32)end
 cpu.spaces.io:write_u8(1,0);p:write_u8(0xe010,1);le(0xe160,0xe150)
 p:write_u8(0xf94b,0x20+k);p:write_u8(0xf95a,0xfe);p:write_u8(0xf95b,0xac)
 le(0xf3a7,123);le(0xf3b1,0x0120);p:write_u8(0xf3b6,5);p:write_u8(0xf40e,1);p:write_u8(0xf421,2)
 cpu.state.IX.value=0xf940;cpu.state.SP.value=0xeffe;cpu.state.PC.value=0x5f72
 dbg:command('bpclear')
 for _,pc in ipairs({'0109','00f6','0116','4faf','5f92','5ff1','6039','6064','63a7','192b'})do dbg:command('bp '..pc..':maincpu,1')end
 enabled=true
 for guard=1,1000 do
  cpu.debug:go();repeat emu.wait_next_update()until dbg.execution_state=='stop'
  local pc=cpu.state.PC.value;local a=(cpu.state.AF.value>>8)&255
  if pc==0x63a7 or pc==0x192b then emit('END',pc==0x63a7 and 1 or 0);break
  elseif pc==0x0116 then emit('WAIT',a);tick=tick+a;ret()
  elseif pc==0x5f92 then emit('SPRITE',0x300+a);cpu.state.PC.value=0x5f95;p:write_u8(cpu.state.IY.value,a)
  elseif pc==0x5ff1 or pc==0x6039 or pc==0x6064 then
   emit('REWARD',pc==0x5ff1 and 1 or pc==0x6039 and 3 or 4)
   -- Step past the first instruction, preserving its effect.
   if pc==0x5ff1 then cpu.state.HL.value=p:read_u16(0xf3a7)
   elseif pc==0x6039 then cpu.state.AF.value=(p:read_u8(0xf3b6)<<8)|(cpu.state.AF.value&255)
   else cpu.state.DE.value=0x30 end
   cpu.state.PC.value=pc+3
  else ret()end
  assert(guard<1000)
 end
 enabled=false
end
out:write('COMPLETE\n');out:close();m:exit()
