local m=manager.machine;local cpu=m.devices[':maincpu'];local dbg=m.debugger
local p=cpu.spaces.program;local out=assert(io.open('events.txt','w'))
local function le(a,v) p:write_u8(a,v&255);p:write_u8(a+1,(v>>8)&255) end
local function be(a,v) p:write_u8(a,(v>>8)&255);p:write_u8(a+1,v&255) end
assert(dbg and cpu.state.PC.value==0);dbg.visible_cpu=cpu
for id,c in ipairs(dofile('cases.lua')) do
 for a=0xe000,0xffff do p:write_u8(a,0) end
 for _,r in ipairs({'AF','BC','DE','HL','IX','IY'}) do cpu.state[r].value=0 end
 cpu.spaces.io:write_u8(1,1)
 for i=0,47 do p:write_u8(0xfb60+i,p:read_u8(c.template+i)) end
 be(0xfb61,c.ax);be(0xfb63,c.ay);p:write_u8(0xf400,0x80)
 cpu.state.IX.value=0xfb60;cpu.state.IY.value=0xfca0
 p:write_u8(0xf402,32);be(0xfca1,c.x-(c.kind==0 and 32 or 0));be(0xfca3,c.y)
 p:write_u8(0xfcb0,c.w);p:write_u8(0xfcb1,c.h);p:write_u8(0xf44c,c.w);p:write_u8(0xf44d,c.h)
 p:write_u8(0xf40b,c.w);p:write_u8(0xf40c,c.h);p:write_u8(0xf426,c.alternate)
 if c.kind==2 then be(0xf401,c.x);be(0xf403,c.y) end
 cpu.state.SP.value=0xeffe;le(0xeffe,0x1e17)
 cpu.state.PC.value=c.kind==0 and 0x39bf or c.kind==1 and 0x3acc or 0x3bb7
 dbg:command('bpclear')
 for _,pc in ipairs({0x1e17,0x3c9a,0x3ab5,0x3cfb,0x3ba5,0x3c89}) do dbg:command(string.format('bp %04x:maincpu,1',pc)) end
 cpu.debug:go();repeat emu.wait_next_update() until dbg.execution_state=='stop'
 local pc=cpu.state.PC.value
 local result=pc==0x1e17 and 0 or (pc==0x3c9a or pc==0x3cfb) and 2 or 1
 out:write(string.format('CONTACT|%d|%d|%04x\n',id-1,result,pc))
end
out:write('COMPLETE\n');out:close();m:exit()
