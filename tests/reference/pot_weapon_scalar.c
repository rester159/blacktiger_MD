/* Scalar pot scan before candidate-list batching. */
u8 reference_weapon(s16 x,s16 y,u8 dagger){
 u16 i;if(dagger && (game.frame&1))return 0;
 for(i=0;i<pots_end;i++){
  Pot *p=&pots[i];s16 dx,dy;u16 w=8+(dagger?dagger_width:8),h=8+(dagger?dagger_height:4);
  if(!p->active || p->phase || p->pending || (u16)(p->x-game.cam_x)>=256 || (dagger && (u16)(x-game.cam_x)>=256))continue;
  dx=(u8)(x-game.cam_x)-(u8)(p->x-game.cam_x);dy=(u8)(y-game.cam_y)-(u8)(p->y-game.cam_y);
  if((u16)(dx+w)<=2*w && (u16)(dy+h)<=2*h){p->pending=1;return 1;}
 }return 0;
}
