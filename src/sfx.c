#include "sfx.h"
#include "sfx_data.inc"
SfxSlot sfx_slots[2];
u8 sfx_active,sfx_phase,sfx_request;
u32 sfx_ticks;
static u32 fraction;
static u16 last_tone[3];
static u8 last_volume[4],last_noise;
void sfx_invalidate(void){u8 i;for(i=0;i<3;i++)last_tone[i]=65535;for(i=0;i<4;i++)last_volume[i]=255;last_noise=255;}
static void active(void){sfx_active=sfx_slots[0].active|sfx_slots[1].active;}
void sfx_reset(void){sfx_slots[0]=(SfxSlot){0};sfx_slots[1]=(SfxSlot){0};sfx_active=sfx_phase=sfx_request=0;sfx_ticks=fraction=0;sfx_invalidate();}
static void reset_registers(SfxSlot *s){u8 i;for(i=0;i<11;i++)s->regs[i]=0;s->regs[7]=0xf8;}
static void tone_registers(SfxSlot *s,u8 ch){u16 p=s->pitch[ch]>>4;s->regs[ch*2]=p;s->regs[ch*2+1]=p>>8;}
static void parameters(SfxSlot *s,const SfxOp *op){
 u16 value=op->value;u8 ch;
 if(op->kind<=4){
  ch=op->kind-2;
  if(value!=4095){s->pitch[ch]=value<<4;tone_registers(s,ch);}
  s->pitch_delta[ch]=value?op->delta:0;
 } else if(op->kind<=7){
  ch=op->kind-5;
  if(value && value!=31){s->volume[ch]=value<<4;s->regs[8+ch]=s->volume[ch]>>4;}
  if(!value)s->regs[8+ch]=0;
  s->volume_delta[ch]=value?op->delta:0;
 } else {
  s->noise=(value>>8)<<3;s->mixer=(s->mixer&0xc7)|(value&56);
  s->regs[6]=s->noise>>3;s->regs[7]=s->mixer;s->noise_delta=op->delta;
 }
}
static void load_segment(SfxSlot *s){
 while(s->position<s->track->length){
  const SfxOp *op=&s->track->data[s->position++];
  if(op->kind==9)s->repeat=0;
  else if(op->kind==10){if(++s->repeat!=op->delta)s->position=op->value;}
  else if(op->kind==11){s->active=0;reset_registers(s);return;}
  else if(op->kind==0){
   s->remaining=op->value-1;
   while(s->position<s->track->length){
    op=&s->track->data[s->position];if(op->kind<2 || op->kind>8)break;
    s->position++;parameters(s,op);
   }
   return;
  }
 }
}
static void step(SfxSlot *s){
 u8 ch;s->tick++;
 if(!s->remaining){load_segment(s);return;}
 s->remaining--;
 for(ch=0;ch<3;ch++)if(s->pitch_delta[ch]){s->pitch[ch]+=(s8)s->pitch_delta[ch];tone_registers(s,ch);}
 if(!sfx_phase){
  for(ch=0;ch<3;ch++)if(s->volume_delta[ch]){s->volume[ch]+=s->volume_delta[ch];s->regs[8+ch]=s->volume[ch]>>4;}
  if(s->noise_delta){s->noise+=s->noise_delta;s->regs[6]=s->noise>>3;s->regs[7]=s->mixer;}
 }
}
u8 sfx_start(u8 command){
 const SfxTrack *t;SfxSlot *s;
 if(command==0x1f){sfx_slots[0]=(SfxSlot){0};sfx_slots[1]=(SfxSlot){0};active();return 1;}
 if(command>=64)return 0;t=&sfx_tracks[command];if(!t->data)return 0;
 s=&sfx_slots[(t->flags>>6)&1];
 if(s->active && (s->track->flags&15)>(t->flags&15))return 0;
 *s=(SfxSlot){.track=t,.command=command,.active=1};reset_registers(s);active();return 1;
}
void sfx_timer_step(void){
 u8 i;sfx_phase=(sfx_phase+1)&3;sfx_ticks++;
 for(i=0;i<2;i++)if(sfx_slots[i].active)step(&sfx_slots[i]);
 active();
}
void sfx_advance(u16 frames,u8 pal){
 u32 denominator=pal?61461:1791;
 while(frames--){
  fraction+=pal?308939:7467;
  while(fraction>=denominator){fraction-=denominator;sfx_timer_step();}
 }
}
void sfx_render(u8 pal){
 u16 tones[3]={1,1,1},noise_period=1;u8 volumes[4]={15,15,15,15};
 u8 chosen[3]={255,255,255},levels[6],priority[6],i,j,noise_level=15,noise=4,limit=3;
 if(!sfx_active){for(i=0;i<4;i++)if(last_volume[i]!=15){sfx_volume(i,15);last_volume[i]=15;}return;}
 for(i=0;i<6;i++){
  SfxSlot *s=&sfx_slots[i/3];u8 ch=i%3,level=s->active?sfx_attenuation[s->regs[8+ch]]:15;
  levels[i]=(s->regs[7]&(1<<ch))?15:level;priority[i]=s->active?(s->track->flags&15):0;
  if(s->active && !(s->regs[7]&(8<<ch)) && level<noise_level){noise_level=level;noise_period=s->regs[6]&31;if(!noise_period)noise_period=1;}
 }
 /* Preserve noise pitch using tone 3's clock when a fixed SN divisor cannot.
    Tone/noise AND gating becomes additive; up to two source tones may be lost. */
 if(noise_level<15){
  if(noise_period==16)noise=4;
  else if(noise_period==32)noise=5;
  else {noise=7;limit=2;tones[2]=noise_period;}
  volumes[3]=noise_level;
 }
 for(j=0;j<limit;j++){
  u8 best=255;
  for(i=0;i<6;i++){
   u8 used=0,k;for(k=0;k<j;k++)if(chosen[k]==i)used=1;
   if(!used && levels[i]<15 && (best==255 || levels[i]<levels[best] || (levels[i]==levels[best] && priority[i]>priority[best])))best=i;
  }
  chosen[j]=best;
  if(best!=255){SfxSlot *s=&sfx_slots[best/3];u8 ch=best%3;tones[j]=s->regs[ch*2]|((u16)(s->regs[ch*2+1]&15)<<8);if(!tones[j])tones[j]=1;volumes[j]=levels[best];}
 }
 for(i=0;i<3;i++){
  u16 value=tones[i];if(pal)value=((u32)value*32768+16535)/33070;if(!value)value=1;if(value>1023)value=1023;
  if(value!=last_tone[i]){sfx_tone(i,value);last_tone[i]=value;}
 }
 if(noise!=last_noise){sfx_noise(noise);last_noise=noise;}
 for(i=0;i<4;i++)if(volumes[i]!=last_volume[i]){sfx_volume(i,volumes[i]);last_volume[i]=volumes[i];}
}
