/* Host-side 68000 instruction attribution for the hash-pinned test core.
   Internal offsets are guarded by CPUProfiler before this hook is installed. */
#include <stdint.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
typedef void (*Handler)(void);
static Handler original[65536],*dispatch;
static uint8_t *cpu,*base_cycles;
uint64_t instruction_cycles[0x200000],instruction_counts[0x200000];
static uint32_t word(unsigned offset){return *(uint32_t*)(cpu+offset);}
static void sample(void){
 uint32_t pc=(word(0x2858)-2)&0xffffff,op=word(0x28b4),before=word(0x280c);
 original[op]();
 if(pc<0x400000){instruction_cycles[pc>>1]+=(int32_t)(word(0x280c)-before)+((int64_t)base_cycles[op]*word(0x29c8)>>20);instruction_counts[pc>>1]++;}
}
int profile_begin(void *state,void *table,void *timing){
 cpu=state;dispatch=table;base_cycles=timing;
 long pagesize=sysconf(_SC_PAGESIZE);uintptr_t start=(uintptr_t)table&~(pagesize-1);
 if(mprotect((void*)start,(uintptr_t)table+65536*sizeof(Handler)-start,PROT_READ|PROT_WRITE))return -1;
 memcpy(original,dispatch,sizeof original);
 memset(instruction_cycles,0,sizeof instruction_cycles);memset(instruction_counts,0,sizeof instruction_counts);
 for(unsigned i=0;i<65536;i++)dispatch[i]=sample;
 return 0;
}
void profile_end(void){memcpy(dispatch,original,sizeof original);}
