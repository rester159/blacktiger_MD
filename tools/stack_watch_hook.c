#include <stdint.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
typedef void (*Handler)(void);
static Handler original[65536],*dispatch;
static uint8_t *cpu;
static uint32_t (*reg)(int);
uint32_t lowest=65536,lowest_pc,lowest_sr;
static void sample(void){
 uint32_t op=*(uint32_t*)(cpu+0x28b4),sp=reg(15)&65535;
 if(sp && sp<lowest){lowest=sp;lowest_pc=reg(16);lowest_sr=reg(17);}
 original[op]();
}
int begin(void *state,void *table,void *getreg){
 cpu=state;dispatch=table;reg=getreg;long pagesize=sysconf(_SC_PAGESIZE);uintptr_t start=(uintptr_t)table&~(pagesize-1);
 if(mprotect((void*)start,(uintptr_t)table+65536*sizeof(Handler)-start,PROT_READ|PROT_WRITE))return -1;
 memcpy(original,dispatch,sizeof original);for(unsigned i=0;i<65536;i++)dispatch[i]=sample;return 0;
}
void end(void){memcpy(dispatch,original,sizeof original);}
