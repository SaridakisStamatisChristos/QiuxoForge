// Included from census5_dual_tier_external.cpp after all state/tier primitives.
// POSIX durable occupancy-boundary snapshot format QFCKPT1.
#pragma once
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <limits>

namespace qcheckpoint {
namespace fs = std::filesystem;
static const U FNV_OFFSET=14695981039346656037ULL;
static const U FNV_PRIME=1099511628211ULL;
inline U fnv64(const void* bytes,size_t length){
 const auto *data=static_cast<const unsigned char*>(bytes);
 U h=FNV_OFFSET;
 for(size_t i=0;i<length;i++){h^=data[i];h*=FNV_PRIME;}
 return h;
}
inline void sync_dir(const fs::path& p){
 int fd=::open(p.c_str(),O_RDONLY|O_DIRECTORY);
 if(fd<0)throw runtime_error("checkpoint cannot open directory: "+p.string());
 if(::fsync(fd)!=0){int e=errno;::close(fd);throw runtime_error("checkpoint dir sync: "+string(strerror(e)));}
 ::close(fd);
}
inline void safe_write(const fs::path& p,const void* data,size_t n){
 int fd=::open(p.c_str(),O_CREAT|O_EXCL|O_WRONLY,0600);
 if(fd<0)throw runtime_error("cannot create checkpoint file: "+p.string());
 try{
  io_exact(fd,const_cast<void*>(data),n,0,true);
  if(::fsync(fd)!=0)throw runtime_error("cannot fsync checkpoint file: "+p.string());
 }catch(...){::close(fd);throw;}
 ::close(fd);
}
struct Progress {
 U raw=0,orbits=0,terminal=0,win1=0,unique=0;
};
inline void save(const string &parent,int last_k,int target_cap,const Progress& progress){
 if(last_k>=target_cap)throw runtime_error("cannot snapshot after final tier");
 const int next=last_k+1;
 fs::path root(parent);
 if(!fs::exists(root))fs::create_directories(root);
 if(!fs::is_directory(root))throw runtime_error("checkpoint path is not a directory");
 // Each snapshot has an immutable name and is published by an atomic
 // directory rename only after fsyncing all bitmap files and its manifest.
 fs::path final=root/("checkpoint-"+to_string(next));
 if(fs::exists(final))throw runtime_error("checkpoint generation already exists: "+final.string());
 fs::path stage=root/("checkpoint-"+to_string(next)+".part-"+to_string(::getpid()));
 if(!fs::create_directory(stage))throw runtime_error("checkpoint staging path already exists");
 ostringstream manifest;
 manifest<<"QFCKPT1 5 "<<target_cap<<" "<<next<<" "<<progress.raw<<" "
         <<progress.orbits<<" "<<progress.terminal<<" "<<progress.win1
         <<" "<<progress.unique<<"\n";
 for(int x=0;x<=next;x++){
  int o=next-x;Tier &t=ensure_tier(x,o);
  const U n=t.words*sizeof(U);
  const U checksum=fnv64(t.seen,static_cast<size_t>(n));
  string name="tier-"+to_string(x)+"-"+to_string(o)+".bin";
  safe_write(stage/name,t.seen,static_cast<size_t>(n));
  manifest<<x<<" "<<o<<" "<<n<<" "<<hex<<checksum<<dec<<"\n";
 }
 const string text=manifest.str();
 safe_write(stage/"manifest.txt",text.data(),text.size());
 sync_dir(stage);
 if(::rename(stage.c_str(),final.c_str())!=0)
  throw runtime_error("atomic checkpoint directory rename failed");
 sync_dir(root);
 cerr<<"CHECKPOINT_COMPLETE "<<final.string()<<" next_occupancy="<<next<<"\n";
}
// Checkpoints are saved only after k<cap, preserving ALL k+1 successors.
// Therefore a cap may increase safely (never decrease) upon resume.
inline int load(const string &name,int requested_cap,Progress& progress){
 fs::path dir(name);
 if(!fs::is_directory(dir))throw runtime_error("resume checkpoint directory does not exist");
 ifstream in(dir/"manifest.txt");
 if(!in)throw runtime_error("missing checkpoint manifest");
 string magic;int size=0,stored_cap=0,next=0;
 if(!(in>>magic>>size>>stored_cap>>next>>progress.raw>>progress.orbits
       >>progress.terminal>>progress.win1>>progress.unique)
    ||magic!="QFCKPT1"||size!=5||stored_cap<1||stored_cap>25
    ||requested_cap<stored_cap||next<1||next>stored_cap||next>requested_cap)
  throw runtime_error("checkpoint schema/cap mismatch or truncated header");
 for(int x=0;x<=next;x++){
  int fx=-1,fo=-1;U bytes=0,hash=0;
  if(!(in>>fx>>fo>>bytes>>hex>>hash>>dec))
   throw runtime_error("truncated checkpoint bitmap manifest");
  int o=next-x;
  Tier &t=ensure_tier(x,o);
  const U expected=t.words*sizeof(U);
  if(fx!=x||fo!=o||bytes!=expected)
   throw runtime_error("checkpoint tier dimensions do not match");
  fs::path p=dir/("tier-"+to_string(x)+"-"+to_string(o)+".bin");
  int fd=::open(p.c_str(),O_RDONLY|O_NOFOLLOW);
  if(fd<0)throw runtime_error("missing or symlinked checkpoint tier bitmap");
  struct stat st{};
  if(::fstat(fd,&st)!=0||st.st_size<0||static_cast<U>(st.st_size)!=bytes){
   ::close(fd);throw runtime_error("checkpoint tier bitmap size mismatch");
  }
  try{io_exact(fd,t.seen,static_cast<size_t>(bytes),0,false);}
  catch(...){::close(fd);throw;}
  ::close(fd);
  if(fnv64(t.seen,static_cast<size_t>(bytes))!=hash)
   throw runtime_error("checkpoint bitmap checksum mismatch");
 }
 string extra;
 if(in>>extra)throw runtime_error("checkpoint has unexpected trailing rows");
 if(!in.eof())throw runtime_error("checkpoint manifest parsing failed");
 cerr<<"CHECKPOINT_RESUMED "<<name<<" next_occupancy="<<next<<"\n";
 return next;
}
} // namespace qcheckpoint
