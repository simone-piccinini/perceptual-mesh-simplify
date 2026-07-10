// meshopt attribute-quadric simplification driver (offline reference eval, C1).
// Reads OBJ, builds per-vertex area-weighted normals as a weighted attribute,
// runs meshopt_simplifyWithAttributes to a target vertex count, writes OBJ.
// Build: g++ -O2 -std=c++17 -I. mo_driver.cpp simplifier.cpp -o mo_driver
// Usage: ./mo_driver in.obj out.obj targetV normalWeight
#include "meshoptimizer.h"
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <vector>
#include <string>
#include <cstring>

struct V3 { float x,y,z; };

int main(int argc, char** argv){
    if(argc<5){ std::fprintf(stderr,"usage: %s in.obj out.obj targetV normalWeight\n",argv[0]); return 1; }
    const char* in=argv[1]; const char* out=argv[2];
    int targetV=atoi(argv[3]); float nw=atof(argv[4]);

    std::vector<V3> pos; std::vector<unsigned int> idx;
    { FILE* f=fopen(in,"r"); if(!f){ std::fprintf(stderr,"open %s failed\n",in); return 1; }
      char line[512];
      while(fgets(line,sizeof line,f)){
        if(line[0]=='v'&&line[1]==' '){ V3 p; sscanf(line+2,"%f %f %f",&p.x,&p.y,&p.z); pos.push_back(p); }
        else if(line[0]=='f'&&line[1]==' '){
            unsigned int a,b,c;
            // supports "f i j k" and "f i/x j/x k/x"
            if(sscanf(line+2,"%u/%*u/%*u %u/%*u/%*u %u/%*u/%*u",&a,&b,&c)==3 ||
               sscanf(line+2,"%u/%*u %u/%*u %u/%*u",&a,&b,&c)==3 ||
               sscanf(line+2,"%u %u %u",&a,&b,&c)==3){
                idx.push_back(a-1); idx.push_back(b-1); idx.push_back(c-1);
            }
        }
      }
      fclose(f); }
    size_t vcount=pos.size(), icount=idx.size();
    std::fprintf(stderr,"loaded V=%zu F=%zu\n",vcount,icount/3);

    // per-vertex area-weighted normals (the appearance attribute)
    std::vector<float> nrm(vcount*3,0.f);
    for(size_t i=0;i<icount;i+=3){
        unsigned int a=idx[i],b=idx[i+1],c=idx[i+2];
        float ux=pos[b].x-pos[a].x,uy=pos[b].y-pos[a].y,uz=pos[b].z-pos[a].z;
        float vx=pos[c].x-pos[a].x,vy=pos[c].y-pos[a].y,vz=pos[c].z-pos[a].z;
        float nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx; // area-weighted (unnormalized cross)
        for(unsigned int t:{a,b,c}){ nrm[t*3]+=nx; nrm[t*3+1]+=ny; nrm[t*3+2]+=nz; }
    }
    for(size_t v=0;v<vcount;v++){ float* n=&nrm[v*3]; float l=std::sqrt(n[0]*n[0]+n[1]*n[1]+n[2]*n[2]); if(l>1e-20f){n[0]/=l;n[1]/=l;n[2]/=l;} }

    float attr_weights[3]={nw,nw,nw};
    // target index (face) count: closed manifold F~2V -> target_index = 3*2*targetV, then meshopt lands near targetV
    size_t target_index = (size_t)(3*2*(size_t)targetV);
    if(target_index>icount) target_index=icount;
    std::vector<unsigned int> res(icount);
    float result_error=0.f;
    size_t nres=meshopt_simplifyWithAttributes(
        res.data(), idx.data(), icount,
        &pos[0].x, vcount, sizeof(V3),
        nrm.data(), sizeof(float)*3, attr_weights, 3,
        /*vertex_lock*/nullptr, target_index, /*target_error*/1e30f,
        /*options*/0, &result_error);
    res.resize(nres);

    // compact used vertices
    std::vector<int> remap(vcount,-1); std::vector<V3> ov; std::vector<unsigned int> of;
    for(unsigned int id:res){ if(remap[id]<0){ remap[id]=(int)ov.size(); ov.push_back(pos[id]); } of.push_back(remap[id]); }
    std::fprintf(stderr,"meshopt out V=%zu F=%zu (target_index=%zu err=%.4g)\n",ov.size(),of.size()/3,target_index,result_error);

    FILE* g=fopen(out,"w"); if(!g){ std::fprintf(stderr,"write %s failed\n",out); return 1; }
    for(auto&p:ov) std::fprintf(g,"v %.9g %.9g %.9g\n",p.x,p.y,p.z);
    for(size_t i=0;i<of.size();i+=3) std::fprintf(g,"f %u %u %u\n",of[i]+1,of[i+1]+1,of[i+2]+1);
    fclose(g);
    return 0;
}
