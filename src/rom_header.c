#include <genesis.h>

__attribute__((externally_visible))
const ROMHeader rom_header = {
#if (MODULE_MEGAWIFI  && (MEGAWIFI_IMPLEMENTATION == MEGAWIFI_IMPLEMENTATION_MW_CART))
    "SEGA MEGAWIFI   ",
#elif (ENABLE_BANK_SWITCH != 0)
    "SEGA MEGA DRIVE ",
#else
    "SEGA MEGA DRIVE ",
#endif
    "ASTRA 2026     ",
    "BLACK TIGER ASTRA                               ",
    "BLACK TIGER ASTRA                               ",
    "GM 00000000-00",
    0x000,
    "JD              ",
    0x00000000,
#if (ENABLE_BANK_SWITCH != 0)
    0x003FFFFF,
#else
    0x003FFFFF,
#endif
    0x00FF0000,
    0x00FFFFFF,
    "RA",
    0xF820,
    0x00200001,
    0x002007FF,
    "            ",
    "NATIVE SGDK DEVELOPMENT BUILD          ",
    "JUE             "
};
