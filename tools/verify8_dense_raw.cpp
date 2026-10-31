// Independent unsymmetrized 5x5 Quixo BFS via combinatorial dense rank.
// NO D4, NO QuixoForge imports, NO optimized bitboard move implementation.
// Compact exact rank: choose occupied positions (colex), encode marks, append turn.
// Compile: c++ -O3 -std=c++17 tools/verify8_dense_raw.cpp -o /tmp/qf-dense
// Run: /tmp/qf-dense 8 700000000
#include <array>
#include <cstdint>
#include <iostream>
#include <vector>
#include <chrono>
#include <stdexcept>
#include <algorithm>
#include <string>
using U=uint64_t;
constexpr U MASK=(1ULL<<25)-1;
struct M {int cell,step,length;};
std::vector<M> moves;
uint32_t choose[26][10]{};
U offsets[10]{};
void init(int cap){
 choose[0][0]=1;
 for(int i=1;i<=25;i++){
  choose[i][0]=1;
  for(int j=1;j<=std::min(i,9);j++)choose[i][j]=choose[i-1][j]+choose[i-1][j-1];
 }
 for(int k=0;k<=cap;k++)offsets[k+1]=offsets[k]+2ULL*choose[25][k]*(1ULL<<k);
 for(int i=0;i<25;i++){
  int r=i/5,c=i%5;
  if(r!=0&&r!=4&&c!=0&&c!=4)continue;
  if(c>0)moves.push_back({i,-1,c});
  if(c<4)moves.push_back({i,1,4-c});
  if(r>0)moves.push_back({i,-5,r});
  if(r<4)moves.push_back({i,5,4-r});
 }
 if(moves.size()!=44)throw std::runtime_error("illegal Quixo move geometry");
}
// Lossless inverse of the compact 32-bit occupied-subset/color/turn rank.
void decode_rank(uint32_t index,std::array<int8_t,25>&b,bool&turn){
 U rank=index;int k=0;
 while(k<9&&rank>=offsets[k+1])++k;
 if(k>8)throw std::runtime_error("rank exceeds cap eight");
 U payload=rank-offsets[k];turn=payload&1;payload>>=1;
 U color=payload&((1ULL<<k)-1),combo=payload>>k;
 b.fill(0);
 int pos=24;
 for(int j=k;j>=1;j--){
  while(pos>=j&&choose[pos][j]>combo)pos--;
  if(pos<j-1)throw std::runtime_error("invalid colex rank");
  b[pos]=(color&(1ULL<<(j-1)))?1:-1;
  combo-=choose[pos][j];
  pos--;
 }
 if(combo)throw std::runtime_error("nonzero unrank remainder");
}
int winner(const std::array<int8_t,25>&b,bool oturn){
 bool x=false,o=false;
 for(int r=0;r<5;r++){
  int a=b[5*r],c=b[r];
  if(a&&b[5*r+1]==a&&b[5*r+2]==a&&b[5*r+3]==a&&b[5*r+4]==a){x|=a==1;o|=a==-1;}
  if(c&&b[5+r]==c&&b[10+r]==c&&b[15+r]==c&&b[20+r]==c){x|=c==1;o|=c==-1;}
 }
 int a=b[0],c=b[4];
 if(a&&b[6]==a&&b[12]==a&&b[18]==a&&b[24]==a){x|=a==1;o|=a==-1;}
 if(c&&b[8]==c&&b[12]==c&&b[16]==c&&b[20]==c){x|=c==1;o|=c==-1;}
 if(x&&o)return oturn?-1:1;
 return x?1:o?-1:0;
}
U encode_rank(const std::array<int8_t,25>&b,bool turn){
 U combination=0,color=0;int k=0;
 for(int i=0;i<25;i++){
  int mark=b[i];if(!mark)continue;
  ++k;combination+=choose[i][k];
  if(mark==1)color|=1ULL<<(k-1);
 }
 return offsets[k]+((combination*(1ULL<<k)+color)<<1)+U(turn);
}
int main(int argc,char**argv){
 try{
  int cap=argc>1?std::stoi(argv[1]):8;
  if(cap<0||cap>8)throw std::runtime_error("cap must be between 0 and 8");
  U budget=argc>2?std::stoull(argv[2]):700000000ULL;
  if(budget<1||budget>700000000ULL)throw std::runtime_error("invalid raw-state budget");
  init(cap);
  U bits=offsets[cap+1];
  if(bits>0xFFFFFFFFULL)throw std::runtime_error("combinatorial rank exceeds uint32 scope");
  for(int k=0;k<=cap;k++){
   const U base=offsets[k],span=offsets[k+1]-base;
   for(U j=0;j<1000;j++){
    const U idx=base+(span*j)/1000;
    std::array<int8_t,25> probe{};bool pt=false;
    decode_rank(static_cast<uint32_t>(idx),probe,pt);
    if(encode_rank(probe,pt)!=idx)throw std::runtime_error("rank/unrank bijection false");
   }
  }
  std::vector<U> visited((bits+63)/64,0ULL);
  auto add=[&](U idx){
   if(idx>=bits)throw std::runtime_error("invalid combinatorial index");
   U &slot=visited[idx>>6],mask=1ULL<<(idx&63);
   if(slot&mask)return false;
   slot|=mask;return true;
  };
  std::vector<uint32_t> q;
  q.reserve(cap==8?650000000ULL:cap==7?120000000ULL:cap==6?20000000ULL:3000000ULL);
  q.push_back(0);add(0);
  std::array<int8_t,25> b{},next{};
  U layer[9]{},terminal[9]{},win_raw[9]{},unique_raw[9]{},candidate=0,retained=0;
  auto start=std::chrono::steady_clock::now();
  for(size_t j=0;j<q.size();j++){
   bool turn=false;
   decode_rank(q[j],b,turn);
   int k=0;for(int8_t v:b)k+=(v!=0);
   if(k>cap)throw std::runtime_error("domain escape");
   layer[k]++;
   if(winner(b,turn)!=0){terminal[k]++;continue;}
   int current=turn?-1:1;
   int own_marks=0,winning_actions=0;
   for(int8_t v:b)own_marks+=(v==current);
   for(const M&m:moves){
    if(b[m.cell]!=0&&b[m.cell]!=current)continue;
    candidate++;
    const bool in_domain=!(k==cap&&b[m.cell]==0);
    if(own_marks<4&&!in_domain)continue;
    next=b;
    for(int t=0;t<m.length;t++)
      next[m.cell+t*m.step]=b[m.cell+(t+1)*m.step];
    next[m.cell+m.length*m.step]=current;
    // Crucial: also inspect winning actions that ADD a new cube at cap.
    // Their successor is outside the reachable-root cap but remains a
    // valid tactical solution for this root.
    if(own_marks>=4&&winner(next,!turn)==current)winning_actions++;
    if(!in_domain)continue;
    retained++;
    const U idx=encode_rank(next,!turn);
    if(add(idx)){
      if(q.size()>=budget)throw std::runtime_error("raw state budget reached: incomplete");
      q.push_back(static_cast<uint32_t>(idx));
    }
   }
   if(winning_actions){
     win_raw[k]++;
     if(winning_actions==1)unique_raw[k]++;
   }
   if(j&&j%20000000==0)
     std::cerr<<"raw verified "<<j<<" states; discovered "<<q.size()<<"\n";
  }
  constexpr U EXPECT[9]={1,16,468,11812,187164,2055382,16353436,99693740,484731202};
  constexpr U TERMINALS[9]={0,0,0,0,0,0,552,15748,247248};
  constexpr U WIN_RAW[9]={0,0,0,0,0,936,29140,480424,5071268};
  constexpr U UNIQUE_RAW[9]={0,0,0,0,0,360,9508,161920,1777204};
  for(int k=0;k<=cap;k++){
   if(layer[k]!=EXPECT[k])throw std::runtime_error("independent raw occupancy mismatch");
   if(terminal[k]!=TERMINALS[k])throw std::runtime_error("independent raw terminal mismatch");
   if(win_raw[k]!=WIN_RAW[k])throw std::runtime_error("independent raw winning positions mismatch");
   if(unique_raw[k]!=UNIQUE_RAW[k])throw std::runtime_error("independent raw unique positions mismatch");
  }
  std::cout<<"{\"schema\":1,\"cap\":"<<cap<<",\"raw_states\":"<<q.size()<<",\"by_occupancy\":[";
  for(int k=0;k<=cap;k++){if(k)std::cout<<",";std::cout<<layer[k];}
  std::cout<<"],\"terminal_by_occupancy\":[";
  for(int k=0;k<=cap;k++){if(k)std::cout<<",";std::cout<<terminal[k];}
  std::cout<<"],\"win_in_one_by_occupancy\":[";
  for(int k=0;k<=cap;k++){if(k)std::cout<<",";std::cout<<win_raw[k];}
  std::cout<<"],\"unique_win_in_one_by_occupancy\":[";
  for(int k=0;k<=cap;k++){if(k)std::cout<<",";std::cout<<unique_raw[k];}
  std::cout<<"],\"candidate_edges\":"<<candidate<<",\"retained_edges\":"<<retained
   <<",\"structural_bits\":"<<bits
   <<",\"seconds\":"<<std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count()<<"}\n";
 }catch(const std::exception&e){std::cerr<<"ERROR: "<<e.what()<<"\n";return 2;}
}
