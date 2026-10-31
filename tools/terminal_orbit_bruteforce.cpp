// Independent brute-force D4-fixed terminal board colorings.
// No inclusion-exclusion, no QuixoForge imports. Nonidentity symmetries
// have <=15 cycles, so at most 3^15=14,348,907 boards per symmetry.
#include <array>
#include <vector>
#include <iostream>
#include <cstdint>
#include <cassert>
using U=uint32_t;
using L=long long;
int main(){
 const std::array<L,8> EXPECT_TERM={0,390,435502,390,4841478,1677606,4841478,1677606};
 const std::array<L,8> EXPECT_NONTERM_BOTH={0,1616,1149024,1616,9475712,12622208,9475712,12622208};
 std::array<U,12> lines{};
 int n=0;
 for(int r=0;r<5;r++){for(int c=0;c<5;c++)lines[n]|=1u<<(5*r+c);n++;}
 for(int c=0;c<5;c++){for(int r=0;r<5;r++)lines[n]|=1u<<(5*r+c);n++;}
 for(int j=0;j<5;j++){lines[10]|=1u<<(6*j);lines[11]|=1u<<(4+4*j);}
 for(int g=1;g<8;g++){
  std::array<int,25> perm{};
  for(int i=0;i<25;i++){
    int r=i/5,c=i%5;if(g>=4)c=4-c;
    for(int j=0;j<g%4;j++){int rr=c,cc=4-r;r=rr;c=cc;}
    perm[i]=5*r+c;
  }
  std::array<int,25> assigned{};assigned.fill(-1);
  std::vector<U> cycles;
  for(int i=0;i<25;i++)if(assigned[i]==-1){
   int k=cycles.size(),j=i;
   U mask=0;
   while(assigned[j]==-1){assigned[j]=k;mask|=1u<<j;j=perm[j];}
   cycles.push_back(mask);
  }
  L size=1;for(size_t i=0;i<cycles.size();i++)size*=3;
  L terminal=0,nonterm_both=0;
  for(L code=0;code<size;code++){
   L q=code;U X=0,O=0;
   for(U mask:cycles){const int color=q%3;q/=3;
     if(color==1)X|=mask;else if(color==2)O|=mask;}
   bool ended=false;
   for(U line:lines)if((line&X)==line||(line&O)==line){ended=true;break;}
   terminal+=ended;nonterm_both+=!ended&&X&&O;
  }
  assert(terminal==EXPECT_TERM[g]);
  assert(nonterm_both==EXPECT_NONTERM_BOTH[g]);
  std::cout<<"g="<<g<<" fixed_terminal="<<terminal
           <<" fixed_nonterminal_both_colors="<<nonterm_both<<"\n";
 }
 std::cout<<"PASS: seven independent direct D4 symmetry-fixed enumerations\n";
}
