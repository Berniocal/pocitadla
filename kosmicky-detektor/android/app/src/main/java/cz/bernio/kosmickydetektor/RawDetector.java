package cz.bernio.kosmickydetektor;

import android.media.Image;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.Arrays;

/** Pixel-level detector on native 16-bit RAW_SENSOR mosaics (no demosaicing). */
public final class RawDetector {
    public static final int CALIBRATION_FRAMES = 18;
    private static final int MAX_ROI_WIDTH=2048, MAX_ROI_HEIGHT=1536;
    private int roiW,roiH,roiX,roiY,fullWidth,fullHeight;
    private int frames=0,cal=0,overbright=0, threshold=80, rejected=0;
    private float[] mean,m2;
    private int[] sample,queue,lastHit;
    private byte[] flags;

    public void reset() {
        roiW=roiH=roiX=roiY=fullWidth=fullHeight=frames=cal=overbright=rejected=0;
        mean=null;m2=null;sample=null;flags=null;queue=null;lastHit=null;
    }
    public void setThreshold(int value) {threshold=Math.max(20,Math.min(500,value));}
    public boolean ready(){return cal>=CALIBRATION_FRAMES;}
    public int frames(){return frames;}
    public int calibrated(){return cal;}
    public int rejected(){return rejected;}
    public int roiWidth(){return roiW;}
    public int roiHeight(){return roiH;}
    public int offsetX(){return roiX;}
    public int offsetY(){return roiY;}

    private void initialize(Image image) {
        fullWidth=image.getWidth();fullHeight=image.getHeight();
        roiW=Math.min(MAX_ROI_WIDTH,fullWidth);
        roiH=Math.min(MAX_ROI_HEIGHT,fullHeight);
        roiX=(fullWidth-roiW)/2;roiY=(fullHeight-roiH)/2;
        int n=roiW*roiH;
        mean=new float[n];m2=new float[n];sample=new int[n];
        queue=new int[n];lastHit=new int[n];flags=new byte[n];
    }
    private void read(Image image) {
        if(sample==null || fullWidth!=image.getWidth() || fullHeight!=image.getHeight()) {
            initialize(image);
        }
        Image.Plane plane=image.getPlanes()[0];
        ByteBuffer b=plane.getBuffer().duplicate().order(ByteOrder.LITTLE_ENDIAN);
        int row=plane.getRowStride(),step=plane.getPixelStride();
        if(step!=2)throw new IllegalStateException("RAW_SENSOR pixelStride="+step+" (očekávám 2)");
        for(int y=0;y<roiH;y++) {
            int off=(y+roiY)*row+roiX*step;
            int start=y*roiW;
            for(int x=0;x<roiW;x++) sample[start+x]=b.getShort(off+x*step)&65535;
        }
    }
    public Detector.Analysis process(Image image) {
        read(image);
        frames++;
        if(!ready()){
            cal++;
            for(int i=0;i<sample.length;i++){
                float delta=sample[i]-mean[i];
                mean[i]+=delta/cal;
                m2[i]+=delta*(sample[i]-mean[i]);
            }
            return new Detector.Analysis(new ArrayList<>(),false);
        }
        int count=0,abnormallyBright=0;
        for(int i=0;i<sample.length;i++){
            float sigma=(float)Math.sqrt(Math.max(0,m2[i]/(cal-1)));
            float delta=sample[i]-mean[i];
            // Learn the baseline per native Bayer pixel, without averaging neighboring colors.
            float minimum=Math.max(threshold,9*sigma);
            if(delta>minimum && delta>0 && sigma<Math.max(100,threshold*2)) {
                flags[i]=1;
                count++;
            } else flags[i]=0;
            if(delta>threshold*3)abnormallyBright++;
        }
        if(count>Math.max(300,sample.length/500) || abnormallyBright>sample.length/100){
            rejected++;return new Detector.Analysis(new ArrayList<>(),true);
        }
        ArrayList<Detector.Hit> hits=new ArrayList<>();
        for(int i=0;i<sample.length;i++){
            if(flags[i]!=1)continue;
            int head=0,tail=1;queue[0]=i;flags[i]=2;
            int peak=0,peakIndex=i,cluster=0;boolean repeats=false;
            while(head<tail) {
                int pos=queue[head++];
                int x=pos%roiW,y=pos/roiW;
                cluster++;
                int d=(int)(sample[pos]-mean[pos]);
                if(d>peak){peak=d;peakIndex=pos;}
                if(frames-lastHit[pos]<=3 && lastHit[pos]!=0)repeats=true;
                for(int dy=-1;dy<=1;dy++) {
                    int yy=y+dy;if(yy<0||yy>=roiH)continue;
                    for(int dx=-1;dx<=1;dx++){
                        int xx=x+dx;if(xx<0||xx>=roiW)continue;
                        int near=yy*roiW+xx;
                        if(flags[near]==1){flags[near]=2;queue[tail++]=near;}
                    }
                }
            }
            for(int k=0;k<tail;k++)lastHit[queue[k]]=frames;
            // Subpixel noise, long rows of leakage and recurring pixels are rejected.
            if(!repeats && cluster<=130 && (cluster>=2 || peak>threshold*2)){
                hits.add(new Detector.Hit(roiX+peakIndex%roiW,
                    roiY+peakIndex/roiW,cluster,peak));
                if(hits.size()>=8)break;
            }
        }
        return new Detector.Analysis(hits,false);
    }
    /** Grayscale preview of differential RAW signal, not a demosaiced photograph. */
    public byte[] differencePatch(int fullX,int fullY,int size) {
        byte[] result=new byte[size*size];
        int x0=fullX-roiX-size/2,y0=fullY-roiY-size/2;
        for(int y=0;y<size;y++)for(int x=0;x<size;x++){
            int xx=x0+x,yy=y0+y;if(xx<0||yy<0||xx>=roiW||yy>=roiH)continue;
            int p=yy*roiW+xx;
            int brightness=(int)Math.max(0,Math.min(255,(sample[p]-mean[p])*1.5f));
            result[y*size+x]=(byte)brightness;
        }
        return result;
    }
}
