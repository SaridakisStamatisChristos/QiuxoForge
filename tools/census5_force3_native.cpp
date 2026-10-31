// Independent native 5x5 reachable-orbit and immediate-tactic census.
// Compile: c++ -O3 -std=c++17 -Wall -Wextra -pedantic tools/census5_native.cpp -o /tmp/quixoforge-census5
// Run:     /tmp/quixoforge-census5 7 20000000
// X starts. All legal same-occupancy cycles; stop at terminal positions.
// D4 rotates/reflects board only; no color swap; turn belongs to the key.
// Each selected cube + insertion endpoint is a distinct winning action.
#include <array>
#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <vector>
#include <chrono>
#include <stdexcept>
#include <string>
using U = uint64_t;
using I = uint32_t;
constexpr I FULL=(1u<<25)-1;
struct S {I x=0,o=0; bool turn=false;}; // false X, true O
struct Move {int cell=0,end=0,len=0;std::array<int,5> path{};I mask=0;};
std::vector<Move> moves;
std::array<I,12> lines{};
std::array<std::array<std::array<I,256>,4>,8> table{};
inline int stones(I x){return __builtin_popcount(x);}
void setup(){
 int k=0;
 for(int r=0;r<5;r++){I b=0;for(int c=0;c<5;c++)b|=1u<<(5*r+c);lines[k++]=b;}
 for(int c=0;c<5;c++){I b=0;for(int r=0;r<5;r++)b|=1u<<(5*r+c);lines[k++]=b;}
 I d=0,e=0;for(int j=0;j<5;j++){d|=1u<<(6*j);e|=1u<<(4+4*j);}lines[k++]=d;lines[k++]=e;
 for(int cell=0;cell<25;cell++){
   int r=cell/5,c=cell%5;
   if(r!=0&&r!=4&&c!=0&&c!=4)continue;
   const std::array<std::pair<int,char>,4> dirs{{{-1,'L'},{1,'R'},{-5,'U'},{5,'D'}}};
   for(auto [step,dir]:dirs){
     if((dir=='L'&&c==0)||(dir=='R'&&c==4)||(dir=='U'&&r==0)||(dir=='D'&&r==4))continue;
     int n=(dir=='L'?c:dir=='R'?4-c:dir=='U'?r:4-r);
     Move m;m.cell=cell;m.len=n+1;m.end=cell+n*step;
     for(int i=0;i<=n;i++){m.path[i]=cell+i*step;m.mask|=1u<<m.path[i];}
     moves.push_back(m);
   }
 }
 if(moves.size()!=44)throw std::runtime_error("incorrect legal path geometry");
 for(int g=0;g<8;g++){
   int dest[25];for(int idx=0;idx<25;idx++){
     int r=idx/5,c=idx%5;
     if(g>=4)c=4-c;
     for(int j=0;j<g%4;j++){int nr=c,nc=4-r;r=nr;c=nc;}
     dest[idx]=5*r+c;
   }
   for(int chunk=0;chunk<4;chunk++){
     int width=std::min(8,25-8*chunk);
     for(int val=0;val<(1<<width);val++){
       I bits=0;for(int j=0;j<width;j++)if(val&(1<<j))bits|=1u<<dest[chunk*8+j];
       table[g][chunk][val]=bits;
     }
   }
 }
}
inline I transform(I mask,int g){auto &t=table[g];return t[0][mask&255]|t[1][(mask>>8)&255]|t[2][(mask>>16)&255]|t[3][mask>>24];}
inline U pack(S s){return U(s.x)|(U(s.o)<<25)|(U(s.turn)<<50);}
inline S unpack(U z){return {I(z&FULL),I((z>>25)&FULL),bool((z>>50)&1)};}
inline U canon(S s){
 U best=~U(0);
 for(int g=0;g<8;g++){U z=pack({transform(s.x,g),transform(s.o,g),s.turn});if(z<best)best=z;}
 return best;
}
inline int orbsize(S s){
 int stab=0;for(int g=0;g<8;g++)if(transform(s.x,g)==s.x&&transform(s.o,g)==s.o)stab++;
 if(stab!=1&&stab!=2&&stab!=4&&stab!=8)throw std::runtime_error("invalid D4 stabilizer");
 return 8/stab;
}
inline int who(S s){
 bool wx=false,wo=false;
 for(I line:lines){wx|=(s.x&line)==line;wo|=(s.o&line)==line;}
 if(wx&&wo)return s.turn?-1:1; // last mover loses when both lines exist
 return wx?1:wo?-1:0;
}
inline S apply(S s,const Move& m){
 I x=s.x&~m.mask,o=s.o&~m.mask;
 for(int j=0;j<m.len-1;j++){
  I src=1u<<m.path[j+1],dest=1u<<m.path[j];
  if(s.x&src)x|=dest;else if(s.o&src)o|=dest;
 }
 if(!s.turn)x|=1u<<m.end;else o|=1u<<m.end;
 return {x,o,!s.turn};
}
// Exhaustive, non-heuristic attacker-defender-attacker finite-horizon search.
// Tactical children may add cubes beyond the enumeration's root cap.
inline bool has_immediate_win(S s){
 if(who(s)!=0)return false;
 const I own=s.turn?s.o:s.x,enemy=s.turn?s.x:s.o;
 if(stones(own)<4)return false;
 const int actor=s.turn?-1:1;
 for(const Move&m:moves)
   if(!(enemy&(1u<<m.cell))&&who(apply(s,m))==actor)return true;
 return false;
}
inline int forced_win_by_three_first_actions(S s){
 if(who(s)!=0)return 0;
 const I own=s.turn?s.o:s.x,enemy=s.turn?s.x:s.o;
 if(stones(own)<3)return 0;
 const int actor=s.turn?-1:1;
 int count=0;
 for(const Move&m:moves){
  if(enemy&(1u<<m.cell))continue;
  if(stones(own)==3&&((own|enemy)&(1u<<m.cell)))continue;
  S after=apply(s,m);
  int winner1=who(after);
  if(winner1==actor){count++;continue;}
  if(winner1==-actor)continue;
  bool forced=true;
  for(const Move&d:moves){
   if((after.turn?after.x:after.o)&(1u<<d.cell))continue;
   S reply=apply(after,d);
   int winner2=who(reply);
   if(winner2==actor)continue;
   if(winner2==-actor||!has_immediate_win(reply)){
      forced=false;break;
   }
  }
  if(forced)count++;
 }
 return count;
}
struct Counts {
 U raw[9]{},orbits[9]{},terminal[9]{},terminalOrbits[9]{};
 U win1Raw[9]{},win1Orbits[9]{},uniq1Raw[9]{},uniq1Orbits[9]{};
 U orbitSize[9]{},candidates=0,retained=0,new3Orbits=0,new3Raw=0,unique3Orbits=0,unique3Raw=0;
};
Counts solve(int cap,U maxorbits){
 Counts totals;
 // Zero is reserved for the empty hash slot. The only zero state is
 // the initial X-to-play empty board, already explicitly in the queue.
 const size_t HSIZE = (cap>=8?1ULL<<27:cap>=7?1ULL<<25:cap==6?1ULL<<23:cap==5?1ULL<<20:1ULL<<17);
 std::vector<U> tab(HSIZE,0);
 U count=1;
 auto insert=[&](U key)->bool{
   if(!key)return false;
   U z=key+0x9e3779b97f4a7c15ULL;
   z=(z^(z>>30))*0xbf58476d1ce4e5b9ULL;
   z=(z^(z>>27))*0x94d049bb133111ebULL;
   size_t pos=(z^(z>>31)) & (HSIZE-1);
   size_t probes=0;
   while(tab[pos] && tab[pos]!=key){
     if(++probes>=HSIZE)throw std::runtime_error("hash capacity exhausted");
     pos=(pos+1)&(HSIZE-1);
   }
   if(tab[pos]==key)return false;
   tab[pos]=key;count++;return true;
 };
 std::vector<U> queue;queue.reserve(cap>=8?80000000:cap>=7?16000000:cap==6?3000000:400000);
 queue.push_back(0);
 for(size_t p=0;p<queue.size();p++){
   S s=unpack(queue[p]);int k=stones(s.x|s.o),os=orbsize(s);
   if(k>cap)throw std::runtime_error("occupancy boundary escape");
   bool terminal=who(s)!=0;
   totals.raw[k]+=os;totals.orbits[k]++;totals.orbitSize[os]++;
   if(terminal){totals.terminal[k]+=os;totals.terminalOrbits[k]++;continue;}
   int wins=0;
   for(const Move &m:moves){
     if((s.turn?s.x:s.o)&(1u<<m.cell))continue;
     totals.candidates++;
     S c=apply(s,m);
     if(who(c)==(s.turn?-1:1))wins++;
     if(k==cap && !((s.x|s.o)&(1u<<m.cell)))continue;
     totals.retained++;
     U cn=canon(c);
     if(insert(cn)){
       if(count>maxorbits)throw std::runtime_error("orbit budget exceeded; report incomplete");
       queue.push_back(cn);
     }
   }
   if(wins){totals.win1Raw[k]+=os;totals.win1Orbits[k]++;
     if(wins==1){totals.uniq1Raw[k]+=os;totals.uniq1Orbits[k]++;}}
   if(!wins && stones(s.turn?s.o:s.x)>=3){
     const int forced=forced_win_by_three_first_actions(s);
     if(forced){
       std::cerr<<"F3|"<<s.x<<"|"<<s.o<<"|"<<(s.turn?1:0)<<"|"<<forced<<"|"<<os<<"\n";
       totals.new3Orbits++;totals.new3Raw+=os;
       if(forced==1){totals.unique3Orbits++;totals.unique3Raw+=os;}
     }
   }
 }
 return totals;
}
int main(int argc,char**argv){
 try{
 int cap=argc>1?std::stoi(argv[1]):6;
 if(cap<0||cap>7)throw std::runtime_error("depth3 roots occupancy must be 0..7");
 U maxorbits=argc>2?std::stoull(argv[2]):20000000ULL;
 if(maxorbits<1||maxorbits>100000000ULL)throw std::runtime_error("orbit budget must be 1..100000000");
 setup();auto start=std::chrono::steady_clock::now();Counts C=solve(cap,maxorbits);
 U a=0,b=0,z=0,w=0,u=0,v=0,t=0,tt=0;
 std::cout<<"{\"schema\":1,\"cap\":"<<cap<<",\"occupancies\":[";
 for(int k=0;k<=cap;k++){
  if(k)std::cout<<",";
  std::cout<<"{\"k\":"<<k<<",\"reachable_states\":"<<C.raw[k]
   <<",\"d4_orbits\":"<<C.orbits[k]
   <<",\"terminal_states\":"<<C.terminal[k]
   <<",\"terminal_orbits\":"<<C.terminalOrbits[k]
   <<",\"win_in_one_states\":"<<C.win1Raw[k]
   <<",\"win_in_one_orbits\":"<<C.win1Orbits[k]
   <<",\"unique_win_in_one_states\":"<<C.uniq1Raw[k]
   <<",\"unique_win_in_one_orbits\":"<<C.uniq1Orbits[k]<<"}";
  a+=C.raw[k];b+=C.orbits[k];z+=C.win1Raw[k];w+=C.win1Orbits[k];
  u+=C.uniq1Raw[k];v+=C.uniq1Orbits[k];t+=C.terminal[k];tt+=C.terminalOrbits[k];
 }
 std::cout<<"],\"reachable_states\":"<<a<<",\"d4_orbits\":"<<b
  <<",\"terminal_states\":"<<t<<",\"terminal_orbits\":"<<tt
  <<",\"win_in_one_states\":"<<z<<",\"win_in_one_orbits\":"<<w
  <<",\"unique_win_in_one_states\":"<<u<<",\"unique_win_in_one_orbits\":"<<v
  <<",\"candidate_edges_repr\":"<<C.candidates
  <<",\"retained_edges_repr\":"<<C.retained
  <<",\"orbit_sizes\":{\"1\":"<<C.orbitSize[1]<<",\"2\":"<<C.orbitSize[2]
  <<",\"4\":"<<C.orbitSize[4]<<",\"8\":"<<C.orbitSize[8]
  <<"},\"new_exactly_three_orbits\":"<<C.new3Orbits
  <<",\"new_exactly_three_raw\":"<<C.new3Raw
  <<",\"unique_exactly_three_orbits\":"<<C.unique3Orbits
  <<",\"unique_exactly_three_raw\":"<<C.unique3Raw
  <<",\"seconds\":"<<std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count()<<"}\n";
 }catch(const std::exception&e){std::cerr<<"ERROR: "<<e.what()<<"\n";return 2;}
}
