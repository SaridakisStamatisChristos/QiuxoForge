// QuixoForge: exact two-color fixed-point tier census (5x5, two players).
// Independent algorithm from the packed global-hash and raw dense-queue audits.
// Build: c++ -std=c++17 -O3 tools/census5_dual_tier.cpp -o /tmp/qf-tiers
// Run: /tmp/qf-tiers 9 >k9.jsonl
// External-memory variant: per-tier perfect-rank visited bitsets are mmap-backed
// scratch files; a buffered pread/pwrite FIFO stores the exact same-tier closure.
// Scratch files are unlinked on creation and never affect published counts.
// The old in-memory dual-tier solver remains an independent regression oracle.
#include <array>
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <vector>
#include <cerrno>
#include <cstring>
#include <string>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
using namespace std;
using U=uint64_t;using I=uint32_t;
struct S{I x=0,o=0;bool turn=false;};
struct M{int cell=0,end=0,len=0;array<int,5>path{};I mask=0;};
vector<M> moves;array<I,12> lines{};array<array<array<I,256>,4>,8> lookup{};
U C[26][26]{};
// The executable is deliberately Linux/POSIX-specific: mmap + pread/pwrite.
static string scratch_dir;
static U mapped_live=0, mapped_peak=0, queue_peak=0;
static int scratch_fd(const char *tag){
 string tmpl=scratch_dir+"/quixo-"+tag+"-XXXXXX";
 vector<char> name(tmpl.begin(),tmpl.end());name.push_back('\0');
 int fd=mkstemp(name.data());
 if(fd<0)throw runtime_error("cannot create scratch file: "+string(strerror(errno)));
 if(unlink(name.data())!=0){int err=errno;close(fd);throw runtime_error("cannot unlink scratch file: "+string(strerror(err)));}
 return fd;
}
static void io_exact(int fd,void *data,size_t length,U offset,bool writing){
 auto *ptr=reinterpret_cast<unsigned char*>(data);
 size_t done=0;
 while(done<length){
  ssize_t n=writing?::pwrite(fd,ptr+done,length-done,static_cast<off_t>(offset+done)):
                     ::pread(fd,ptr+done,length-done,static_cast<off_t>(offset+done));
  if(n<0&&errno==EINTR)continue;
  if(n<=0)throw runtime_error(string(writing?"scratch write failed: ":"scratch read failed: ")+(n==0?"short I/O":strerror(errno)));
  done+=static_cast<size_t>(n);
 }
}
struct Tier{
 int x=0,o=0;U size=0,words=0;U *seen=nullptr;int fd=-1;
 Tier(int xx,int oo,U universe):x(xx),o(oo),size(universe){
  words=(size+63)/64;U bytes=words*sizeof(U);
  if(!bytes||bytes>static_cast<U>(INT64_MAX))throw runtime_error("unsupported tier bitmap size");
  fd=scratch_fd("bitmap");
  // Explicit reservation: ENOSPC is reported as an error, not a delayed SIGBUS.
  int err=posix_fallocate(fd,0,static_cast<off_t>(bytes));
  if(err){::close(fd);fd=-1;throw runtime_error("cannot reserve tier scratch storage: "+string(strerror(err)));}
  void *p=mmap(nullptr,static_cast<size_t>(bytes),PROT_READ|PROT_WRITE,MAP_SHARED,fd,0);
  if(p==MAP_FAILED){err=errno;::close(fd);fd=-1;throw runtime_error("mmap failed: "+string(strerror(err)));}
  seen=static_cast<U*>(p);
  mapped_live+=bytes;mapped_peak=max(mapped_peak,mapped_live);
 }
 Tier(const Tier&)=delete;Tier&operator=(const Tier&)=delete;
 void release(){
  if(seen){
   U bytes=words*sizeof(U);
   if(munmap(seen,static_cast<size_t>(bytes))!=0)throw runtime_error("munmap failed");
   seen=nullptr;mapped_live-=bytes;
  }
  if(fd>=0){::close(fd);fd=-1;}
 }
 ~Tier(){if(seen){munmap(seen,static_cast<size_t>(words*sizeof(U)));mapped_live-=words*sizeof(U);}if(fd>=0)::close(fd);}
};
Tier* tiers[26][26]{};
unique_ptr<Tier> storage[26][26]{};
int cap=7;
static Tier& ensure_tier(int x,int o){
 if(x<0||o<0||x+o>cap)throw runtime_error("attempted to write outside occupancy cap");
 if(!storage[x][o]){
  U universe=2*C[25][x]*C[25-x][o];
  storage[x][o]=make_unique<Tier>(x,o,universe);
  tiers[x][o]=storage[x][o].get();
 }
 if(!tiers[x][o]->seen)throw runtime_error("attempted to revisit finalized tier");
 return *tiers[x][o];
}
// One exact FIFO per active tier. Data lives on scratch storage; the two
// fixed-size buffers require just 512 KiB of queue RAM irrespective of tier.
struct DiskQueue{
 static constexpr size_t BLOCK=32768;
 int fd=-1;array<U,BLOCK> pending{},cache{};
 U appended=0,written=0,read=0,cache_start=0,cache_end=0;
 size_t pending_n=0;
 DiskQueue():fd(scratch_fd("fifo")){}
 DiskQueue(const DiskQueue&)=delete;DiskQueue&operator=(const DiskQueue&)=delete;
 ~DiskQueue(){if(fd>=0)::close(fd);}
 void flush(){
  if(!pending_n)return;
  io_exact(fd,pending.data(),pending_n*sizeof(U),written*sizeof(U),true);
  written+=pending_n;pending_n=0;
 }
 void push(U item){
  pending[pending_n++]=item;++appended;
  if(pending_n==BLOCK)flush();
 }
 bool pop(U& item){
  if(read==appended)return false;
  if(read>=cache_end){
   flush();
   cache_start=read;
   U n=min<U>(BLOCK,appended-read);
   io_exact(fd,cache.data(),static_cast<size_t>(n*sizeof(U)),read*sizeof(U),false);
   cache_end=read+n;
  }
  item=cache[static_cast<size_t>(read-cache_start)];++read;
  return true;
 }
 U size()const{return appended;}
 U bytes()const{return appended*sizeof(U);}
};
inline int pop(I x){return __builtin_popcount(x);}
void setup(){
 C[0][0]=1;
 for(int n=1;n<=25;n++){C[n][0]=1;for(int k=1;k<=n;k++)C[n][k]=C[n-1][k-1]+C[n-1][k];}
 int k=0;
 for(int r=0;r<5;r++){I z=0;for(int c=0;c<5;c++)z|=1u<<(5*r+c);lines[k++]=z;}
 for(int c=0;c<5;c++){I z=0;for(int r=0;r<5;r++)z|=1u<<(5*r+c);lines[k++]=z;}
 I d=0,e=0;for(int j=0;j<5;j++){d|=1u<<(6*j);e|=1u<<(4+4*j);}lines[k++]=d;lines[k++]=e;
 for(int cell=0;cell<25;cell++){
  int r=cell/5,c=cell%5;if(r!=0&&r!=4&&c!=0&&c!=4)continue;
  for(auto sd:array<pair<int,char>,4>{{{-1,'L'},{1,'R'},{-5,'U'},{5,'D'}}}){
   int step=sd.first;char dir=sd.second;
   if((dir=='L'&&c==0)||(dir=='R'&&c==4)||(dir=='U'&&r==0)||(dir=='D'&&r==4))continue;
   int len=(dir=='L'?c:dir=='R'?4-c:dir=='U'?r:4-r)+1;
   M m;m.cell=cell;m.end=cell+(len-1)*step;m.len=len;
   for(int i=0;i<len;i++){m.path[i]=cell+i*step;m.mask|=1u<<m.path[i];}
   moves.push_back(m);
  }
 }
 if(moves.size()!=44)throw runtime_error("bad move geometry");
 for(int g=0;g<8;g++){
  int dest[25];for(int idx=0;idx<25;idx++){
   int r=idx/5,c=idx%5;if(g>=4)c=4-c;
   for(int j=0;j<g%4;j++){int nr=c,nc=4-r;r=nr;c=nc;}dest[idx]=5*r+c;
  }
  for(int block=0;block<4;block++){
   int width=min(8,25-8*block);
   for(int bits=0;bits<(1<<width);bits++){
    I z=0;for(int j=0;j<width;j++)if(bits&(1<<j))z|=1u<<dest[block*8+j];
    lookup[g][block][bits]=z;
   }
  }
 }
 // Bitmaps are allocated lazily only when predecessor tiers first reach them.
}
inline I transform(I z,int g){
 auto &t=lookup[g];return t[0][z&255]|t[1][(z>>8)&255]|t[2][(z>>16)&255]|t[3][z>>24];
}
inline U pack(S s){return U(s.x)|(U(s.o)<<25)|(U(s.turn)<<50);}
inline S unpack(U z){return {I(z&((1u<<25)-1)),I((z>>25)&((1u<<25)-1)),bool((z>>50)&1)};}
inline S canon(S s){
 U best=~U(0);for(int g=0;g<8;g++)
  best=min(best,pack({transform(s.x,g),transform(s.o,g),s.turn}));
 return unpack(best);
}
inline int orbit(S s){
 int fixed=0;for(int g=0;g<8;g++)fixed+=(transform(s.x,g)==s.x&&transform(s.o,g)==s.o);
 if(fixed!=1&&fixed!=2&&fixed!=4&&fixed!=8)throw runtime_error("invalid D4 stabilizer");
 return 8/fixed;
}
inline int winner(S s){
 bool x=false,o=false;
 for(I mask:lines){x|=(s.x&mask)==mask;o|=(s.o&mask)==mask;}
 if(x&&o)return s.turn?-1:1; // mover who created both lines loses; side to move wins
 return x?1:o?-1:0;
}
inline S apply(S s,const M&m){
 I x=s.x&~m.mask,o=s.o&~m.mask;
 for(int j=0;j<m.len-1;j++){
  I src=1u<<m.path[j+1],dst=1u<<m.path[j];
  if(s.x&src)x|=dst;else if(s.o&src)o|=dst;
 }
 if(s.turn)o|=1u<<m.end;else x|=1u<<m.end;
 return {x,o,!s.turn};
}
inline U rank_bits(I bits){
 U rank=0;int j=0;
 while(bits){int i=__builtin_ctz(bits);bits&=bits-1;rank+=C[i][++j];}
 return rank;
}
inline I unrank_bits(U rank,int n,int k){
 I bits=0;int pos=n-1;
 for(int j=k;j>=1;j--){
  while(pos>=j&&C[pos][j]>rank)--pos;
  if(pos<j-1)throw runtime_error("bad unrank");
  bits|=1u<<pos;rank-=C[pos][j];--pos;
 }
 if(rank)throw runtime_error("nonzero unrank remainder");
 return bits;
}
inline U rank_state(S s,int x,int o){
 U xr=rank_bits(s.x);I available=((1u<<25)-1)^s.x;
 U orank=0;int j=0,index=0;
 while(available){
  int p=__builtin_ctz(available);available&=available-1;
  if(s.o&(1u<<p))orank+=C[index][++j];index++;
 }
 if(j!=o)throw runtime_error("bad O count");
 return ((xr*C[25-x][o]+orank)<<1)|s.turn;
}
inline S unrank_state(U rank,int x,int o){
 bool turn=rank&1;rank>>=1;U block=C[25-x][o],xr=rank/block,orrank=rank%block;
 I xb=unrank_bits(xr,25,x),ob=unrank_bits(orrank,25-x,o);
 I available=((1u<<25)-1)^xb,O=0;int i=0;
 while(available){int p=__builtin_ctz(available);available&=available-1;
  if(ob&(1u<<i))O|=1u<<p;i++;}
 return {xb,O,turn};
}
inline bool mark(S s,int x,int o){
 Tier &t=ensure_tier(x,o);U rank=rank_state(s,x,o);
 if(rank>=t.size)throw runtime_error("rank escapes tier");
 U &word=t.seen[rank>>6],mask=1ull<<(rank&63);
 if(word&mask)return false;
 word|=mask;return true;
}
#include "quixo_checkpoint.hpp"

int main(int argc,char**argv){
 try{
  cap=argc>1?stoi(argv[1]):7;
  if(cap<0||cap>25)throw runtime_error("cap must be 0..25");
  scratch_dir=argc>2?argv[2]:(getenv("TMPDIR")?getenv("TMPDIR"):"/tmp");
  string checkpoint_root,resume_dir;
  int checkpoint_at=-1,stop_after=-1;
  for(int i=3;i<argc;i++){
   string opt=argv[i];
   if(opt=="--checkpoint"&&i+1<argc)checkpoint_root=argv[++i];
   else if(opt=="--checkpoint-at"&&i+1<argc)checkpoint_at=stoi(argv[++i]);
   else if(opt=="--stop-after"&&i+1<argc)stop_after=stoi(argv[++i]);
   else if(opt=="--resume"&&i+1<argc)resume_dir=argv[++i];
   else throw runtime_error("invalid checkpoint option: "+opt);
  }
  if(checkpoint_at==-1&&!checkpoint_root.empty())checkpoint_at=cap-1;
  if((checkpoint_at>=0&&checkpoint_root.empty())||
     (!checkpoint_root.empty()&&(checkpoint_at<0||checkpoint_at>=cap))||
     (stop_after>=0&&(stop_after!=checkpoint_at||checkpoint_root.empty())))
   throw runtime_error("checkpoint-at must be 0..cap-1 and stop-after must equal checkpoint-at");
  struct stat st{};
  if(stat(scratch_dir.c_str(),&st)!=0||!S_ISDIR(st.st_mode)||access(scratch_dir.c_str(),W_OK|X_OK)!=0)
   throw runtime_error("scratch directory must exist and be writable");
  setup();
  U allRaw=0,allOrbits=0,allTerminal=0,allWin1=0,allUnique=0;
  int start_k=0;
  if(!resume_dir.empty()){
   qcheckpoint::Progress progress;
   start_k=qcheckpoint::load(resume_dir,cap,progress);
   allRaw=progress.raw;allOrbits=progress.orbits;
   allTerminal=progress.terminal;allWin1=progress.win1;allUnique=progress.unique;
   if(checkpoint_at>=0&&checkpoint_at<start_k)
    throw runtime_error("checkpoint-at must follow resumed tier");
  }else mark(S{},0,0);
  auto start=chrono::steady_clock::now();
  for(int k=start_k;k<=cap;k++){
   U levelRaw=0,levelOrbits=0,levelTerminal=0,levelWin1=0;
   for(int x=0;x<=k;x++){
    int o=k-x;Tier&t=ensure_tier(x,o);DiskQueue queue;
    for(U i=0;i<t.words;i++){
     U bits=t.seen[i];
     while(bits){int j=__builtin_ctzll(bits);bits&=bits-1;U rank=64*i+j;
      if(rank<t.size){S s=unrank_state(rank,x,o);queue.push(pack(s));}
     }
    }
    U current;
    while(queue.pop(current)){
     S s=unpack(current);
     if(pop(s.x)!=x||pop(s.o)!=o)throw runtime_error("wrong tier");
     int weight=orbit(s);levelRaw+=weight;levelOrbits++;
     if(winner(s)){levelTerminal+=weight;continue;}
     int actor=s.turn?-1:1,wins=0;I enemy=s.turn?s.x:s.o;bool canwin=pop(s.turn?s.o:s.x)>=4;
     for(const M&m:moves){
      I bit=1u<<m.cell;if(enemy&bit)continue;
      S next=apply(s,m);if(canwin&&winner(next)==actor)wins++;
      bool increase=!(bit&(s.x|s.o));
      if(k==cap&&increase)continue;
      S key=canon(next);int nx=x+(!s.turn&&increase),no=o+(s.turn&&increase);
      if(mark(key,nx,no)&&!increase)queue.push(pack(key));
     }
     if(wins){levelWin1++;allWin1++;}if(wins==1)allUnique++;
    }
    queue_peak=max(queue_peak,queue.bytes());
    cerr<<"tier K="<<k<<" X="<<x<<" O="<<o<<" exact_orbits="<<queue.size()
        <<" scratch_queue_bytes="<<queue.bytes()<<"\n";
    t.release();
   }
   allRaw+=levelRaw;allOrbits+=levelOrbits;allTerminal+=levelTerminal;
   double sec=chrono::duration<double>(chrono::steady_clock::now()-start).count();
   cout<<"{\"occupancy\":"<<k<<",\"raw_states\":"<<levelRaw<<",\"orbits\":"
       <<levelOrbits<<",\"terminal_raw\":"<<levelTerminal
       <<",\"win1_orbits\":"<<levelWin1<<",\"elapsed_seconds\":"<<sec<<"}"<<endl;
   if(k==checkpoint_at){
    qcheckpoint::Progress progress{allRaw,allOrbits,allTerminal,allWin1,allUnique};
    qcheckpoint::save(checkpoint_root,k,cap,progress);
    if(stop_after==k)return 0; // No completed-census footer on a partial run.
   }
  }
  cout<<"{\"cap\":"<<cap<<",\"total_raw\":"<<allRaw
      <<",\"total_orbits\":"<<allOrbits
      <<",\"total_terminal_raw\":"<<allTerminal
      <<",\"total_win1_orbits\":"<<allWin1
      <<",\"total_unique_win1_orbits\":"<<allUnique
      <<",\"peak_mapped_bitmap_bytes\":"<<mapped_peak
      <<",\"peak_queue_disk_bytes\":"<<queue_peak<<"}"<<endl;
 }catch(const exception&e){cerr<<"ERROR "<<e.what()<<"\n";return 2;}
}
