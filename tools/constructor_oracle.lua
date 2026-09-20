-- Offline constructor ownership census. The shipped cartridge never executes this code.
local m=manager.machine;local cpu=m.devices[':maincpu'];local dbg=m.debugger
local p=cpu.spaces.program;local ports=cpu.spaces.io
local out=assert(io.open('events.txt','w'))
local function emit(s) out:write(s,'\n');out:flush() end
local function le(a,v) p:write_u8(a,v&255);p:write_u8(a+1,(v>>8)&255) end
local function hex(a,n) local t={} for i=0,n-1 do t[#t+1]=string.format('%02x',p:read_u8(a+i)) end return table.concat(t) end
local cases=dofile('cases.lua');assert(dbg and cpu.state.PC.value==0);dbg.visible_cpu=cpu
for _,case in ipairs(cases) do
 for _,profile in ipairs({0,3,19,29}) do
  for a=0xe000,0xffff do p:write_u8(a,0) end
  for _,r in ipairs({'AF','BC','DE','HL','IX','IY'}) do cpu.state[r].value=0 end
  ports:write_u8(1,case.bank);p:write_u8(0xe0e3,case.bank)
  le(0xe160,0xe150);p:write_u8(0xe010,1)
  le(0xe923,128);le(0xe925,128);le(0xe927,0xec58)
  p:write_u8(0xec59,profile);p:write_u8(0xe930,0x21)
  for a=0xea10,0xea50 do p:write_u8(a,0x10) end
  p:write_u8(0xf402,128);p:write_u8(0xf404,128)
  cpu.state.SP.value=0xeffe;le(0xeffe,0x1e17);cpu.state.PC.value=case.pc
  dbg:command('bpclear');dbg:command('bp 1e17:maincpu,1')
  for _,pc in ipairs(case.copies) do dbg:command(string.format('bp %04x:maincpu,(de==ix)||(de==f940&&((bc==60)||(bc==c0)))',pc)) end
  local stops=0;local copied={}
  while true do
   cpu.debug:go()
   local updates=0
   repeat emu.wait_next_update();updates=updates+1;assert(updates<1000,'constructor runaway') until dbg.execution_state=='stop'
   local pc=cpu.state.PC.value
   if pc==0x1e17 then break end
   stops=stops+1;assert(stops<2048,'too many copies')
   local n=cpu.state.BC.value;assert(n<2048)
   if cpu.state.HL.value<0xc000 then emit(string.format('COPY|%d|%d|%04x|%04x|%04x|%04x|%s',case.id,profile,pc,cpu.state.HL.value,cpu.state.DE.value,cpu.state.IX.value,hex(cpu.state.HL.value,n)));copied[cpu.state.DE.value]=n end
   -- Resume skips the currently stopped breakpoint in MAME.
  end
  local actors={}
  local addresses={} for a in pairs(copied) do addresses[#addresses+1]=a end table.sort(addresses)
  for _,a in ipairs(addresses) do actors[#actors+1]=string.format('%04x:%s',a,hex(a,copied[a])) end
  emit(string.format('RESULT|%d|%d|%s|%s',case.id,profile,hex(0xec58,4),table.concat(actors,',')))
  for _,a in ipairs(addresses) do
   local n=copied[a];local cursor=p:read_u8(a+30)+256*p:read_u8(a+31)
   if p:read_u8(a)==0x80 and (n==32 or n==48) and p:read_u8(a+12)<16 and cursor>0x100 then
    dbg:command('bpclear');dbg:command('bp 1e17:maincpu,1')
    cpu.state.IX.value=a;cpu.state.SP.value=0xeffe;le(0xeffe,0x1e17)
    cpu.state.PC.value=n==32 and 0x2fe7 or 0x32c7;cpu.debug:go()
    local updates=0
    repeat emu.wait_next_update();updates=updates+1;assert(updates<1000,'frame runaway') until dbg.execution_state=='stop'
    local display=p:read_u8(a+26)*256+p:read_u8(a+27)
    emit(string.format('FRAME|%d|%d|%04x|%s|%s',case.id,profile,a,hex(a,n),hex(display,n==32 and 4 or 16)))
   end
  end
 end
end
emit('COMPLETE');out:close();m:exit()
