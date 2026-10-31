// Independent UNSYMMETRIZED tuple-array verification for 5x5 X-first Quixo.
// Not linked to QuixoForge or the D4-native enumerator. No bitboard moves.
// Compile: c++ -O3 -std=c++17 -Wall -Wextra -pedantic tools/verify5_native_raw.cpp -o /tmp/qf-raw
// Run: /tmp/qf-raw 6
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <vector>
#include <chrono>
#include <stdexcept>
#include <algorithm>
#include <string>
using U=uint64_t;
constexpr U MASK=(1ULL<<25)-1;
struct P{int origin,step,count;};
std::vector<P> patterns;
void initialize(){
 for(int r=0;r<5;r++)for(int c=0;c<5;c++){
  if(r!=0&&r!=4&&c!=0&&c!=4)continue;
  int i=5*r+c;
  if(c>0)patterns.push_back({i,-1,c});
  if(c<4)patterns.push_back({i,1,4-c});
  if(r>0)patterns.push_back({i,-5,r});
  if(r<4)patterns.push_back({i,5,4-r});
 }
 if(patterns.size()!=44)throw std::runtime_error("bad pattern count");
}
inline void decode(U code,std::array<int8_t,25>& cells){
 U x=code&MASK,o=(code>>25)&MASK;
 for(int i=0;i<25;i++)cells[i]=((x>>i)&1)?1:((o>>i)&1)?-1:0;
}
inline U encode(const std::array<int8_t,25>& cells,bool turn){
 U x=0,o=0;
 for(int i=0;i<25;i++)if(cells[i]==1)x|=1ULL<<i;else if(cells[i]==-1)o|=1ULL<<i;
 return x|(o<<25)|(U(turn)<<50);
}
int winner(const std::array<int8_t,25>& a,bool turn){
 bool winx=false,wino=false;
 for(int r=0;r<5;r++){
  int row=a[5*r],col=a[r];
  if(row){bool ok=true;for(int c=1;c<5;c++)if(a[5*r+c]!=row){ok=false;break;}if(ok){winx|=row==1;wino|=row==-1;}}
  if(col){bool ok=true;for(int c=1;c<5;c++)if(a[5*c+r]!=col){ok=false;break;}if(ok){winx|=col==1;wino|=col==-1;}}
 }
 int d1=a[0],d2=a[4];
 if(d1){bool ok=true;for(int j=1;j<5;j++)if(a[6*j]!=d1)ok=false;if(ok){winx|=d1==1;wino|=d1==-1;}}
 if(d2){bool ok=true;for(int j=1;j<5;j++)if(a[4+4*j]!=d2)ok=false;if(ok){winx|=d2==1;wino|=d2==-1;}}
 if(winx&&wino)return turn?-1:1; // last mover loses
 return winx?1:wino?-1:0;
}
int main(int argc,char**argv){
 try{
 int cap=argc>1?std::stoi(argv[1]):6;
 if(cap<0||cap>6)throw std::runtime_error("allowed cap 0..6");
 U budget=argc>2?std::stoull(argv[2]):22000000ULL;
 if(budget<1||budget>22000000ULL)throw std::runtime_error("raw budget must be 1..22000000");
 initialize();
 auto start=std::chrono::steady_clock::now();
 // Flat exact hash: 0 means unused. Only the root can encode as 0 and it
 // is explicitly preseeded. Load < 60% for cap<=6.
 constexpr size_t HSIZE=1ULL<<25;
 std::vector<U> tab(HSIZE,0);
 U count=1;
 auto insert=[&](U key)->bool{
   if(key==0)return false;
   U z=key+0x9e3779b97f4a7c15ULL;
   z=(z^(z>>30))*0xbf58476d1ce4e5b9ULL;
   z=(z^(z>>27))*0x94d049bb133111ebULL;
   size_t pos=(z^(z>>31))&(HSIZE-1);
   size_t probes=0;
   while(tab[pos]!=0&&tab[pos]!=key){
      if(++probes>=HSIZE)throw std::runtime_error("hash capacity exceeded");
      pos=(pos+1)&(HSIZE-1);
   }
   if(tab[pos]==key)return false;
   tab[pos]=key;count++;return true;
 };
 std::vector<U> queue;queue.reserve(cap==6?21000000:2500000);queue.push_back(0);
 U by[7]{},term[7]{},candidate=0,inside=0;
 std::array<int8_t,25> board{},copy{};
 for(size_t i=0;i<queue.size();i++){
  U code=queue[i];bool turn=(code>>50)&1;
  decode(code,board);
  int occupied=0;for(auto v:board)occupied+=(v!=0);
  by[occupied]++;
  if(winner(board,turn)!=0){term[occupied]++;continue;}
  int current=turn?-1:1;
  for(const P& m:patterns){
   if(board[m.origin]!=0&&board[m.origin]!=current)continue;
   candidate++;
   if(occupied==cap&&board[m.origin]==0)continue;
   inside++;
   copy=board;
   for(int t=0;t<m.count;t++)copy[m.origin+m.step*t]=board[m.origin+m.step*(t+1)];
   copy[m.origin+m.step*m.count]=current;
   U next=encode(copy,!turn);
   if(insert(next)){
    if(count>budget)throw std::runtime_error("raw graph resource budget exhausted");
    queue.push_back(next);
   }
  }
 }
 static constexpr U EXPECTED[7]={1,16,468,11812,187164,2055382,16353436};
 for(int k=0;k<=cap;k++)if(by[k]!=EXPECTED[k])
   throw std::runtime_error("independent raw occupancy count disagrees");
 if(cap==6&&(candidate!=713951292ULL||inside!=178424208ULL||term[6]!=552ULL))
   throw std::runtime_error("independent raw 6-cube transition/terminal mismatch");
 if(cap==5&&(candidate!=88193892ULL||inside!=17724120ULL))
   throw std::runtime_error("independent raw 5-cube transition mismatch");
 std::cout<<"{\"schema\":1,\"cap\":"<<cap<<",\"raw_states\":"<<count<<",\"by_occupancy\":[";
 for(int k=0;k<=cap;k++){if(k)std::cout<<",";std::cout<<by[k];}
 std::cout<<"],\"terminal_by_occupancy\":[";
 for(int k=0;k<=cap;k++){if(k)std::cout<<",";std::cout<<term[k];}
 std::cout<<"],\"candidate_edges\":"<<candidate<<",\"retained_edges\":"<<inside
  <<",\"seconds\":"<<std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count()<<"}\n";
 }catch(const std::exception&e){std::cerr<<"ERROR: "<<e.what()<<"\n";return 2;}
}
