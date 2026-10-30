// Complete structural 5x5 terminal-board orbit count (NOT reachability).
// Inclusion-exclusion over 12 lines and both winning colors, then Burnside D4.
// g++ -O3 -std=c++17 -Wall -Wextra -pedantic tools/terminal_orbit_bounds.cpp -o /tmp/qt
#include <array>
#include <vector>
#include <iostream>
#include <cstdint>
#include <cassert>
using U=uint32_t;
using Count=long long;
struct Sym {
 int cycles=0;
 std::array<U,12> affected{};
};
Sym symmetry(int g) {
 std::array<int,25> perm{};
 for(int i=0;i<25;i++){
  int r=i/5,c=i%5;
  if(g>=4)c=4-c;
  for(int j=0;j<g%4;j++){int rr=c,cc=4-r;r=rr;c=cc;}
  perm[i]=r*5+c;
 }
 std::array<int,25> cycle{};
 cycle.fill(-1);
 Sym s;
 for(int i=0;i<25;i++)if(cycle[i]==-1){
  int j=i;
  while(cycle[j]==-1){cycle[j]=s.cycles;j=perm[j];}
  s.cycles++;
 }
 std::array<U,12> lines{};
 int n=0;
 for(int r=0;r<5;r++){for(int c=0;c<5;c++)lines[n]|=1u<<(5*r+c);n++;}
 for(int c=0;c<5;c++){for(int r=0;r<5;r++)lines[n]|=1u<<(5*r+c);n++;}
 for(int j=0;j<5;j++){lines[10]|=1u<<(6*j);lines[11]|=1u<<(4+4*j);}
 for(int i=0;i<12;i++)for(int j=0;j<25;j++)
  if(lines[i]&(1u<<j))s.affected[i]|=1u<<cycle[j];
 return s;
}
Count pow3(int n){Count v=1;while(n--)v*=3;return v;}
Count no_winner_fixed(const Sym&s){
 // Each line is either not chosen, forced to X, or forced to O.
 // Inconsistent forced X/O cycles contribute zero.
 Count value=0;
 const auto visit=[&](auto&&self,int j,U X,U O,int sign)->void{
  if(j==12){value+=sign*pow3(s.cycles-__builtin_popcount(X|O));return;}
  self(self,j+1,X,O,sign);
  U line=s.affected[j];
  if(!(line&O))self(self,j+1,X|line,O,-sign);
  if(!(line&X))self(self,j+1,X,O|line,-sign);
 };
 visit(visit,0,0,0,1);
 return value;
}
Count no_winner_mono_fixed(const Sym&s){
 // Independent 2-color (blank/X) line exclusion.
 Count value=0;
 const auto visit=[&](auto&&self,int j,U X,int sign)->void{
  if(j==12){value+=sign*(1LL<<(s.cycles-__builtin_popcount(X)));return;}
  self(self,j+1,X,sign);
  self(self,j+1,X|s.affected[j],-sign);
 };
 visit(visit,0,0,1);
 return value;
}
int main(){
 Count terminal_sum=0,both_nonterminal_sum=0;
 for(int g=0;g<8;g++){
  Sym s=symmetry(g);
  const Count total=pow3(s.cycles),nonterminal=no_winner_fixed(s);
  const Count terminal=total-nonterminal;
  const Count nonterminal_with_both=nonterminal-2*no_winner_mono_fixed(s)+1;
  assert(terminal>=0&&terminal<=total);
  assert(nonterminal_with_both>=0&&nonterminal_with_both<=nonterminal);
  terminal_sum+=terminal;
  both_nonterminal_sum+=nonterminal_with_both;
  std::cout<<"g="<<g<<" cycles="<<s.cycles
           <<" fixed_terminal="<<terminal
           <<" fixed_nonterminal_both_colors="<<nonterminal_with_both<<"\n";
 }
 assert(terminal_sum%8==0&&both_nonterminal_sum%8==0);
 const Count terminal_board_orbits=terminal_sum/8;
 const Count terminal_board_turn_orbits=terminal_sum/4;
 const Count nonterminal_both_board_turn_orbits=both_nonterminal_sum/4;
 // X-first reachable nonterminal monochrome states are exactly:
 // empty initial board (1 orbit) and X-only 1-mark boards (3 orbits).
 const Count reachable_nonterminal_upper=nonterminal_both_board_turn_orbits+4;
 assert(terminal_board_orbits==9860698038LL);
 assert(terminal_board_turn_orbits==19721396076LL);
 assert(nonterminal_both_board_turn_orbits==192103543260LL);
 assert(reachable_nonterminal_upper==192103543264LL);
 std::cout<<"structural_terminal_board_orbits="<<terminal_board_orbits<<"\n";
 std::cout<<"structural_terminal_board_turn_orbits="<<terminal_board_turn_orbits<<"\n";
 std::cout<<"structural_nonterminal_both_colors_board_turn_orbits="<<nonterminal_both_board_turn_orbits<<"\n";
 std::cout<<"reachable_nonterminal_board_turn_orbit_upper_bound="<<reachable_nonterminal_upper<<"\n";
}
