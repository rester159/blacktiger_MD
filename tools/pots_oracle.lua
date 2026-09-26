local m=manager.machine;local cpu=m.devices[':maincpu'];local dbg=m.debugger
local p=cpu.spaces.program;local ports=cpu.spaces.io
local out=assert(io.open('events.txt','w'))
local function le(a,v) p:write_u8(a,v&255);p:write_u8(a+1,(v>>8)&255) end
local function call(pc)
 cpu.state.SP.value=0xeffe;le(0xeffe,0x1e17);cpu.state.PC.value=pc
 local waits=0
 while true do
  dbg:command('bpclear');dbg:command('bp 1e17:maincpu,1');dbg:command('bp 0304:maincpu,1');cpu.debug:go()
  repeat emu.wait_next_update() until dbg.execution_state=='stop'
  if cpu.state.PC.value==0x1e17 then break end
  assert(cpu.state.PC.value==0x304);waits=waits+1
  local saved={} for _,r in ipairs({'AF','BC','DE','HL','IX','IY','SP'}) do saved[r]=cpu.state[r].value end
  -- Run the original RNG update for each frame of the two-frame task yield.
  for tick=1,2 do
   cpu.state.PC.value=0x9b9;dbg:command('bpclear');dbg:command('bp 09c6:maincpu,1');cpu.debug:go()
   repeat emu.wait_next_update() until dbg.execution_state=='stop'
  end
  for r,v in pairs(saved) do cpu.state[r].value=v end
  cpu.state.PC.value=p:read_u16(saved.SP);cpu.state.SP.value=saved.SP+2
 end
 assert(waits==16)
end
assert(dbg and cpu.state.PC.value==0);dbg.visible_cpu=cpu
for id,c in ipairs(dofile('cases.lua')) do
 for a=0xe000,0xffff do p:write_u8(a,0) end
 ports:write_u8(1,6);p:write_u8(0xe0e3,6);p:write_u8(0xf3a1,c.round);le(0xe008,c.seed)
 call(0x242a)
 local values={} for a=0xea10,0xea2f do values[#values+1]=string.format('%02x',p:read_u8(a)) end
 out:write(string.format('SHUFFLE|%d|%s|%d\n',id-1,table.concat(values),p:read_u16(0xe008)))
end
out:write('COMPLETE\n');out:close();m:exit()
