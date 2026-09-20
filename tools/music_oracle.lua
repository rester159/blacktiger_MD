local m=manager.machine;local cpu=m.devices[':audiocpu'];local main=m.devices[':maincpu'];local dbg=m.debugger
local p=cpu.spaces.program;local ioport=main.spaces.io;local out=assert(io.open('events.txt','w'))
local progress=assert(io.open('progress.txt','w'))
local function log(s)progress:write(s,'\n');progress:flush()end
local cmd=dofile('cases.lua').command;local tick=0;local regs={};local selected={0,0};local events={}
local tap=p:install_write_tap(0xe000,0xe003,'music_capture',function(address,data,mask)
 local chip=(address-0xe000)//2
 if address%2==0 then selected[chip+1]=data
 else
  local reg=selected[chip+1];regs[chip*256+reg]=data
  if reg==0x28 or reg>=0x30 then events[#events+1]=string.format('WRITE|%d|%d|%d|%d',tick,chip,reg,data) end
 end
end)
local function le(a,v)p:write_u8(a,v&255);p:write_u8(a+1,(v>>8)&255)end
local function run(pc,stop)
 cpu.state.SP.value=0xc7f0;le(0xc7f0,0x0009);cpu.state.PC.value=pc
 dbg:command('bpclear');dbg:command(string.format('bp %04x:audiocpu,1',stop or 9));cpu.debug:go()
 repeat emu.wait_next_update() until dbg.execution_state=='stop'
 if pc==0 and cpu.state.PC.value==0 then cpu.debug:go();repeat emu.wait_next_update() until dbg.execution_state=='stop' end
 if cpu.state.PC.value~=(stop or 9) then log(string.format('unexpected audio=%x main=%x',cpu.state.PC.value,main.state.PC.value));m:exit();error('wrong stop')end
end
assert(main.state.PC.value==0);dbg.visible_cpu=cpu
main.spaces.program:write_u8(0xe200,0xf3);main.spaces.program:write_u8(0xe201,0x76);main.state.PC.value=0xe200
log("boot");ioport:write_u8(4,0);run(0);log("booted");ioport:write_u8(0,cmd);run(0x01fc);log("command")
local seen={};local finished=false
for n=1,50000 do
 if n%1000==0 then log(tostring(n))end
 tick=n;ioport:write_u8(6,0)
 local key={string.char(p:read_u8(0xc013)&1)}
 for a=0xc100,0xc21f do key[#key+1]=string.char(p:read_u8(a))end
 for chip=0,1 do for reg=0x28,0xb2 do key[#key+1]=string.char(regs[chip*256+reg] or 0)end end
 key=table.concat(key)
 if seen[key] then out:write(string.format('LOOP|%d|%d\n',seen[key],tick));finished=true;break end
 seen[key]=tick
 run(0x039f)
 local active=false;for ch=0,5 do if p:read_u8(0xc100+ch*48)~=0 or p:read_u8(0xc101+ch*48)~=0 then active=true end end
 if not active then out:write(string.format('END|%d\n',tick));finished=true;break end
end
assert(finished,'music did not terminate or repeat')
for _,e in ipairs(events)do out:write(e,'\n')end
out:write('COMPLETE\n');out:close();m:exit()
