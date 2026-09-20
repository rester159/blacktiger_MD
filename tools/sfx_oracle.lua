-- Isolated original SSG effects; only register data leaves this offline capture.
local m=manager.machine;local cpu=m.devices[':audiocpu'];local main=m.devices[':maincpu'];local dbg=m.debugger
local p=cpu.spaces.program;local ioport=main.spaces.io;local out=assert(io.open('events.txt','w'))
local tick=0;local selected={0,0};local events={};local regs={};local enabled=false
local tap=p:install_write_tap(0xe000,0xe003,'sfx_capture',function(address,data,mask)
 local chip=(address-0xe000)//2
 if address%2==0 then selected[chip+1]=data
 else
  local reg=selected[chip+1]
  if reg<14 then regs[chip*16+reg]=data;if enabled then events[#events+1]=string.format('WRITE|%d|%d|%d|%d',tick,chip,reg,data)end end
 end
end)
local function run(pc)
 cpu.state.SP.value=0xc7f0;p:write_u16(0xc7f0,9);cpu.state.PC.value=pc
 dbg:command('bpclear');dbg:command('bp 0009:audiocpu,1');cpu.debug:go()
 repeat emu.wait_next_update()until dbg.execution_state=='stop'
 if pc==0 and cpu.state.PC.value==0 then cpu.debug:go();repeat emu.wait_next_update()until dbg.execution_state=='stop'end
 assert(cpu.state.PC.value==9)
end
assert(main.state.PC.value==0);dbg.visible_cpu=cpu
main.spaces.program:write_u8(0xe200,0xf3);main.spaces.program:write_u8(0xe201,0x76);main.state.PC.value=0xe200
for _,case in ipairs(dofile('cases.lua'))do
 tick=0;regs={};events={};enabled=false;ioport:write_u8(4,0);run(0)
 p:write_u8(0xc022,case.phase);enabled=true;ioport:write_u8(0,case.command);run(0x01fc)
 out:write(string.format('CASE|%d|%d\n',case.command,case.phase))
 local seen={};local finished=false
 for n=1,4096 do
  tick=n;ioport:write_u8(6,0)
  local key={string.char(p:read_u8(0xc022)&3)}
  for a=0xc500,0xc55f do key[#key+1]=string.char(p:read_u8(a))end
  for chip=0,1 do for reg=0,13 do key[#key+1]=string.char(regs[chip*16+reg] or 0)end end
  key=table.concat(key)
  if seen[key]then out:write(string.format('LOOP|%d|%d\n',seen[key],tick));finished=true;break end
  seen[key]=tick;run(0x0a50)
  if p:read_u8(0xc500)==0 and p:read_u8(0xc530)==0 then out:write('END|'..tick..'\n');finished=true;break end
 end
 if not finished then out:write('BOUNDED|'..tick..'\n')end
 for _,line in ipairs(events)do out:write(line,'\n')end
 out:flush()
end
enabled=false;out:write('COMPLETE\n');out:close();m:exit()
