-- Full long effects: source register/private-state checkpoints, no recording stream.
local m=manager.machine;local cpu=m.devices[':audiocpu'];local main=m.devices[':maincpu'];local dbg=m.debugger
local p=cpu.spaces.program;local ioport=main.spaces.io;local out=assert(io.open('events.txt','w'))
local selected={0,0};local regs={}
local tap=p:install_write_tap(0xe000,0xe003,'sfx_long',function(address,data,mask)
 local chip=(address-0xe000)//2
 if address%2==0 then selected[chip+1]=data elseif selected[chip+1]<11 then regs[chip*16+selected[chip+1]]=data end
end)
local function run(pc)
 cpu.state.SP.value=0xc7f0;p:write_u16(0xc7f0,9);cpu.state.PC.value=pc
 dbg:command('bpclear');dbg:command('bp 0009:audiocpu,1');cpu.debug:go()
 repeat emu.wait_next_update()until dbg.execution_state=='stop'
 if pc==0 and cpu.state.PC.value==0 then cpu.debug:go();repeat emu.wait_next_update()until dbg.execution_state=='stop'end
 assert(cpu.state.PC.value==9)
end
local function hex(a,n)local t={} for i=0,n-1 do t[#t+1]=string.format('%02x',p:read_u8(a+i))end return table.concat(t)end
assert(main.state.PC.value==0);dbg.visible_cpu=cpu
main.spaces.program:write_u8(0xe200,0xf3);main.spaces.program:write_u8(0xe201,0x76);main.state.PC.value=0xe200
for id,c in ipairs(dofile('cases.lua'))do
 regs={};ioport:write_u8(4,0);run(0);p:write_u8(0xc022,c.phase);ioport:write_u8(0,c.command);run(0x01fc)
 local slot=c.command==0x14 and 0 or 1;local base=0xc500+slot*48
 for tick=0,40000 do
  if tick>0 then ioport:write_u8(6,0);run(0x0a50)end
  local active=p:read_u8(base)
  if tick%256==0 or p:read_u16(base+0x13)==0 or active==0 then
   local values={};for reg=0,10 do values[#values+1]=string.format('%02x',regs[slot*16+reg] or 0)end
   out:write(string.format('STATE|%d|%d|%s|%s\n',id-1,tick,table.concat(values),hex(base,32)));out:flush()
  end
  if tick>0 and active==0 then out:write(string.format('END|%d|%d\n',id-1,tick));break end
  if tick==40000 then out:write('LIMIT\n');out:close();m:exit();return end
 end
end
out:write('COMPLETE\n');out:close();m:exit()
