// Exact 0..25 occupancy breakdown of structural 5x5 terminal D4 orbits.
// Inclusion-exclusion on all winning lines in X/O, weight by # occupied cells.
// C++17: c++ -O3 tools/terminal_bounds_by_occupancy.cpp -o /tmp/q-byk
#include <array>
#include <vector>
#include <iostream>
#include <cstdint>
#include <algorithm>
#include <cassert>
using U=uint32_t;using C=long long;
using Poly=std::array<C,26>;
struct Sym {int n=0;std::vector<int> width;std::array<U,12> lines{};};
Sym symmetry(int g){
 std::array<int,25> p{};
 for(int i=0;i<25;i++){int r=i/5,c=i%5;if(g>=4)c=4-c;
  for(int j=0;j<g%4;j++){int t=c;c=4-r;r=t;}p[i]=5*r+c;}
 std::array<int,25> cycles{};cycles.fill(-1);Sym out;
 for(int i=0;i<25;i++)if(cycles[i]<0){
  int id=out.n++,j=i,width=0;
  while(cycles[j]<0){cycles[j]=id;width++;j=p[j];}
  out.width.push_back(width);
 }
 std::array<U,12> lines{};int n=0;
 for(int r=0;r<5;r++){for(int c=0;c<5;c++)lines[n]|=1u<<(5*r+c);n++;}
 for(int c=0;c<5;c++){for(int r=0;r<5;r++)lines[n]|=1u<<(5*r+c);n++;}
 for(int j=0;j<5;j++){lines[10]|=1u<<(6*j);lines[11]|=1u<<(4+4*j);}
 for(int j=0;j<12;j++)for(int i=0;i<25;i++)
  if(lines[j]>>i&1u)out.lines[j]|=1u<<cycles[i];
 return out;
}
Poly coefficient(const Sym&s,U marked,int free_color_choices){
 Poly p{};int occupied=0;
 for(int i=0;i<s.n;i++)if(marked>>i&1u)occupied+=s.width[i];
 p[occupied]=1;
 for(int i=0;i<s.n;i++)if(!(marked>>i&1u))
  for(int k=25;k>=s.width[i];k--)
    p[k]+=free_color_choices*p[k-s.width[i]];
 return p;
}
struct Counter {Poly nonterm3{},nonterm2{};};
Counter count(const Sym&s){
 Counter c;
 auto full=[&](auto&&self,int j,U x,U o,int sign)->void{
  if(j==12){Poly p=coefficient(s,x|o,2);
   for(int k=0;k<=25;k++)c.nonterm3[k]+=sign*p[k];return;}
  self(self,j+1,x,o,sign);
  U line=s.lines[j];
  if(!(line&o))self(self,j+1,x|line,o,-sign);
  if(!(line&x))self(self,j+1,x,o|line,-sign);
 };
 full(full,0,0,0,1);
 auto mono=[&](auto&&self,int j,U x,int sign)->void{
  if(j==12){Poly p=coefficient(s,x,1);
   for(int k=0;k<=25;k++)c.nonterm2[k]+=sign*p[k];return;}
  self(self,j+1,x,sign);
  self(self,j+1,x|s.lines[j],-sign);
 };
 mono(mono,0,0,1);
 return c;
}
int main(){
 Poly terminal{},both{};
 for(int g=0;g<8;g++){
  Sym s=symmetry(g);Counter c=count(s);
  Poly all=coefficient(s,0,2);
  for(int k=0;k<=25;k++){
   terminal[k]+=all[k]-c.nonterm3[k];
   both[k]+=c.nonterm3[k]-2*c.nonterm2[k]+(k==0?1:0);
  }
 }
 C tsum=0,bsum=0;
 std::cout<<"k,structural_terminal_board_turn_D4,structural_nonterminal_both_colors_board_turn_D4,reachable_nonterminal_upper\n";
 for(int k=0;k<=25;k++){
  assert(terminal[k]%4==0&&both[k]%4==0);
  C t=terminal[k]/4,b=both[k]/4;
  tsum+=t;bsum+=b;
  std::cout<<k<<","<<t<<","<<b<<","<<(b+(k==0?1:k==1?3:0))<<"\n";
 }
 assert(tsum==19721396076LL&&bsum==192103543260LL);
}
