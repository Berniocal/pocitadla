package cz.bernio.kosmickydetektor;

import java.util.ArrayList;
import java.util.List;

/** Experimental detection of transient bright clusters in covered-camera luma frames. */
public final class Detector {
    public static final class Hit {
        public final int x,y,pixels,peak;
        Hit(int x,int y,int pixels,int peak) {
            this.x=x;this.y=y;this.pixels=pixels;this.peak=peak;
        }
    }
    public static final class Analysis {
        public final List<Hit> hits;
        public final boolean lightLeak;
        Analysis(List<Hit> hits, boolean lightLeak) {
            this.hits=hits;this.lightLeak=lightLeak;
        }
    }

    public static final int CALIBRATION_FRAMES=50;
    private int w=-1,h=-1,cal=0,frames=0;
    private float[] mean, m2;
    private byte[] candidates;
    private int[] queue;
    private long[] recent;
    private int threshold=65;
    private int badFrames=0;
    private boolean ready=false;

    public void setThreshold(int value) { threshold=Math.max(30,Math.min(180,value)); }
    public void reset() {
        w=-1; h=-1; cal=0; frames=0; ready=false; badFrames=0;
        mean=null;m2=null;candidates=null;queue=null;recent=null;
    }
    public boolean isReady() { return ready; }
    public int calibratedFrames() { return cal; }
    public int getFrames() { return frames; }
    public int getBadFrames() { return badFrames; }
    private void prepare(int width,int height) {
        if(w==width && h==height) return;
        w=width;h=height;cal=0;frames=0;ready=false;badFrames=0;
        int size=w*h;
        mean=new float[size];m2=new float[size];candidates=new byte[size];
        queue=new int[size];recent=new long[size];
    }

    public Analysis process(byte[] grey,int width,int height,long time) {
        prepare(width,height);
        frames++;
        int size=w*h;
        if (!ready) {
            cal++;
            for(int i=0;i<size;i++) {
                int pixel=grey[i]&255;
                float diff=pixel-mean[i];
                mean[i]+=diff/cal;
                m2[i]+=diff*(pixel-mean[i]);
            }
            if(cal>=CALIBRATION_FRAMES) ready=true;
            return new Analysis(new ArrayList<>(),false);
        }
        int flagged=0;
        int luminous=0;
        for(int i=0;i<size;i++) {
            int v=grey[i]&255;
            if(v>220) luminous++;
            float delta=v-mean[i];
            float variance=m2[i]/Math.max(1,cal-1);
            float required=Math.max(threshold,(float)(7.0*Math.sqrt(Math.max(0,variance))));
            if(v>75 && delta>required && mean[i]<210) {
                candidates[i]=1;
                flagged++;
            } else {
                candidates[i]=0;
            }
        }
        // A light leak or frame processing jump can brighten thousands of pixels.
        if(flagged>Math.max(150,size/500) || luminous>size/30) {
            badFrames++;
            return new Analysis(new ArrayList<>(),true);
        }

        ArrayList<Hit> hits=new ArrayList<>();
        for(int i=0;i<size;i++) {
            if(candidates[i]!=1)continue;
            int head=0,tail=0;
            queue[tail++]=i;
            candidates[i]=2;
            int pixels=0,maxPeak=0,maxAt=i;
            boolean repeats=false;
            while(head<tail) {
                int position=queue[head++];
                int x=position%w,y=position/w;
                int delta=(int)((grey[position]&255)-mean[position]);
                if(delta>maxPeak){maxPeak=delta;maxAt=position;}
                pixels++;
                if(time-recent[position]<4000L && recent[position]!=0L) repeats=true;
                for(int dy=-1;dy<=1;dy++) {
                    int ny=y+dy;
                    if(ny<0 || ny>=h)continue;
                    for(int dx=-1;dx<=1;dx++) {
                        int nx=x+dx;
                        if(nx<0 || nx>=w)continue;
                        int near=ny*w+nx;
                        if(candidates[near]==1) {
                            candidates[near]=2;
                            queue[tail++]=near;
                        }
                    }
                }
            }
            // Record each transient location only once within a few seconds.
            for(int k=0;k<tail;k++)recent[queue[k]]=time;
            if(!repeats && pixels<=100 && (pixels>=2 || maxPeak>threshold+35)) {
                hits.add(new Hit(maxAt%w,maxAt/w,pixels,maxPeak));
                if(hits.size()>=10)break;
            }
        }
        return new Analysis(hits,false);
    }
}
