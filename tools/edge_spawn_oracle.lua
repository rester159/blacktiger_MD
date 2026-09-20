local m=manager.machine;local cpu=m.devices[':maincpu'];local dbg=m.debugger
local p=cpu.spaces.program;local ports=cpu.spaces.io
local out=assert(io.open('events.txt','w'))
local function le(a,v) p:write_u8(a,v&255);p:write_u8(a+1,(v>>8)&255) end
local function be(a,v) p:write_u8(a,(v>>8)&255);p:write_u8(a+1,v&255) end
local function call(pc)
 cpu.state.SP.value=0xeffe;le(0xeffe,0x1e17);cpu.state.PC.value=pc
 dbg:command('bpclear');dbg:command('bp 1e17:maincpu,1');cpu.debug:go()
 repeat emu.wait_next_update() until dbg.execution_state=='stop'
end
assert(dbg and cpu.state.PC.value==0);dbg.visible_cpu=cpu
local data=dofile('cases.lua')
for id,c in ipairs(data.cases) do
 for a=0xe000,0xffff do p:write_u8(a,0) end
 for _,r in ipairs({'AF','BC','DE','HL','IX','IY'}) do cpu.state[r].value=0 end
 ports:write_u8(1,4);p:write_u8(0xe0e3,4);ports:write_u8(14,1);p:write_u8(0xe0e7,1)
 for bank=0,3 do
  ports:write_u8(13,bank)
  for at=0,4094,2 do
   local n=(bank*4096+at)//2;local y=(((n>>4)&15)|((n>>7)&0x30))*16
   local tile=y>=c.ground and data.solid or data.empty
   p:write_u8(0xc000+at,tile&255);p:write_u8(0xc001+at,(tile>>8)&7)
  end
 end
 le(0xe923,c.x);le(0xe925,c.y);le(0xe927,0xec58);be(0xf401,c.px);be(0xf403,c.py)
 p:write_u8(0xe901,c.face*4);p:write_u8(0xec58,c.primary)
 if c.full==1 then for a=0xf940,0xfc0f,48 do p:write_u8(a,128) end end
 call(0xa4d0)
 out:write(string.format('SPAWN|%d|%d|%d|%d|%d|%d\n',id-1,c.full==1 and 0 or p:read_u8(0xf940),p:read_u8(0xec58),p:read_u8(0xf941)*256+p:read_u8(0xf942),p:read_u8(0xf943)*256+p:read_u8(0xf944),p:read_u8(0xe940)))
end
out:write('COMPLETE\n');out:close();m:exit()
