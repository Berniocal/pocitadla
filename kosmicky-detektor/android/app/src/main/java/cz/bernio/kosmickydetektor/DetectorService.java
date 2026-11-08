package cz.bernio.kosmickydetektor;

import android.Manifest;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ServiceInfo;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.graphics.ImageFormat;
import android.hardware.camera2.*;
import android.hardware.camera2.params.StreamConfigurationMap;
import android.media.Image;
import android.media.ImageReader;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.IBinder;
import android.os.PowerManager;
import android.util.Range;
import android.util.Size;
import android.util.Log;
import java.io.File;
import java.io.FileOutputStream;
import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Locale;

/**
 * Serial single-capture acquisition preserves RAW timestamps and paired Camera2
 * metadata, allows genuine long exposures, and avoids RAW buffer pile-ups.
 */
public final class DetectorService extends Service {
    public static final String START="cz.bernio.kosmickydetektor.START";
    public static final String STOP="cz.bernio.kosmickydetektor.STOP";
    public static final String RECALIBRATE="cz.bernio.kosmickydetektor.RECALIBRATE";
    public static final String PREFS="detector_state";
    private static final int NOTIFICATION_ID=42;
    private final Detector yuvDetector=new Detector();
    private final RawDetector rawDetector=new RawDetector();
    private HandlerThread thread;
    private Handler worker;
    private CameraDevice camera;
    private CameraCaptureSession session;
    private ImageReader reader;
    private EventStore db;
    private PowerManager.WakeLock wakeLock;
    private SharedPreferences prefs;
    private CameraCharacteristics characteristics;
    private CaptureRequest.Builder requestBuilder;
    private Image pendingImage;
    private TotalCaptureResult pendingResult;
    private boolean opening=false,raw=false,wantRaw=true,saveDng=false,manual=false;
    private int captureW=0,captureH=0,desiredExposureMs=1000,desiredIso=400;
    private int sensitivity=80,events=0,dngCount=0,consecutiveErrors=0,frames=0;
    private long startTime=0,lastReport=0,actualExposureNs=0;
    private int actualIso=0;
    private String status="Připraveno",hardwareInfo="";

    @Override public void onCreate() {
        super.onCreate();
        prefs=getSharedPreferences(PREFS,MODE_PRIVATE);
        db=new EventStore(this);
        thread=new HandlerThread("Cosmic-Camera2");
        thread.start();worker=new Handler(thread.getLooper());
        NotificationManager nm=(NotificationManager)getSystemService(NOTIFICATION_SERVICE);
        nm.createNotificationChannel(new NotificationChannel("cosmic_measure",
            "Kosmické měření",NotificationManager.IMPORTANCE_LOW));
    }

    @Override public int onStartCommand(Intent intent,int flags,int startId) {
        if(intent!=null && STOP.equals(intent.getAction())){stopSelf();return START_NOT_STICKY;}
        if(intent!=null && RECALIBRATE.equals(intent.getAction())){
            worker.post(()->{
                yuvDetector.reset();rawDetector.reset();
                status="Nová kalibrace";report();
            });
            return START_NOT_STICKY;
        }
        if(camera!=null||opening)return START_NOT_STICKY;
        wantRaw=intent==null || intent.getBooleanExtra("wantRaw",true);
        saveDng=intent!=null && intent.getBooleanExtra("saveDng",false);
        desiredExposureMs=intent!=null?intent.getIntExtra("exposureMs",1000):1000;
        desiredIso=intent!=null?intent.getIntExtra("iso",400):400;
        sensitivity=intent!=null?intent.getIntExtra("threshold",80):80;
        yuvDetector.setThreshold(sensitivity);
        rawDetector.setThreshold(sensitivity);
        startTime=System.currentTimeMillis();events=dngCount=frames=0;
        status="Otevírám kameru";
        startForeground(NOTIFICATION_ID,notification("Kalibrace a měření"),
            ServiceInfo.FOREGROUND_SERVICE_TYPE_CAMERA);
        PowerManager pm=(PowerManager)getSystemService(POWER_SERVICE);
        wakeLock=pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK,"CosmicDetector:Camera2");
        wakeLock.acquire();report();
        worker.post(this::openCamera);
        return START_NOT_STICKY;
    }

    private Notification notification(String message) {
        Intent open=new Intent(this,MainActivity.class);
        PendingIntent go=PendingIntent.getActivity(this,0,open,
            PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        Intent stop=new Intent(this,DetectorService.class).setAction(STOP);
        PendingIntent cancel=PendingIntent.getService(this,1,stop,
            PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
        return new Notification.Builder(this,"cosmic_measure")
            .setSmallIcon(android.R.drawable.ic_menu_camera)
            .setContentTitle("Kosmický detektor")
            .setContentText(message).setOngoing(true).setContentIntent(go)
            .addAction(new Notification.Action.Builder(android.R.drawable.ic_media_pause,
                "Zastavit",cancel).build()).build();
    }
    private void fail(String reason){
        Log.e("CosmicDetector",reason);status=reason;report();
        worker.postDelayed(this::stopSelf,600);
    }
    private static boolean has(int[] modes,int target){
        if(modes==null)return false;
        for(int mode:modes)if(mode==target)return true;
        return false;
    }
    private static boolean supportsRaw(CameraCharacteristics c) {
        if(!has(c.get(CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES),
                CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_RAW))return false;
        StreamConfigurationMap map=c.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
        return map!=null && map.getOutputSizes(ImageFormat.RAW_SENSOR)!=null;
    }
    private void openCamera(){
        try {
            if(checkSelfPermission(Manifest.permission.CAMERA)!=PackageManager.PERMISSION_GRANTED){
                fail("Chybí povolení fotoaparátu");return;
            }
            CameraManager mgr=(CameraManager)getSystemService(Context.CAMERA_SERVICE);
            String chosen=null,rawId=null;
            CameraCharacteristics backup=null,rawChars=null;
            for(String id:mgr.getCameraIdList()){
                CameraCharacteristics c=mgr.getCameraCharacteristics(id);
                Integer facing=c.get(CameraCharacteristics.LENS_FACING);
                if(facing==null || facing!=CameraCharacteristics.LENS_FACING_BACK)continue;
                StreamConfigurationMap map=c.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
                if(map==null || map.getOutputSizes(ImageFormat.YUV_420_888)==null)continue;
                if(chosen==null){chosen=id;backup=c;}
                if(supportsRaw(c)){rawId=id;rawChars=c;break;}
            }
            if(wantRaw && rawId!=null){chosen=rawId;characteristics=rawChars;raw=true;}
            else{characteristics=backup;raw=false;}
            if(chosen==null||characteristics==null){fail("Nenalezena vhodná zadní kamera");return;}
            StreamConfigurationMap map=characteristics.get(
                CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
            Size[] sizes=map.getOutputSizes(raw?ImageFormat.RAW_SENSOR:ImageFormat.YUV_420_888);
            if(sizes==null||sizes.length==0){fail("Kamera neposkytuje požadovaný formát");return;}
            Size size=raw?chooseRawSize(sizes):chooseYuvSize(sizes);
            captureW=size.getWidth();captureH=size.getHeight();
            reader=ImageReader.newInstance(captureW,captureH,
                raw?ImageFormat.RAW_SENSOR:ImageFormat.YUV_420_888,2);
            reader.setOnImageAvailableListener(source->{
                Image i=null;
                try {
                    i=source.acquireNextImage();
                    if(i==null)return;
                    if(pendingImage!=null){pendingImage.close();pendingImage=null;}
                    pendingImage=i;
                    processPairIfReady();
                } catch(Exception e){
                    if(i!=null && i!=pendingImage)i.close();
                    fail("Nepodařilo se přečíst snímek: "+e.getMessage());
                }
            },worker);
            opening=true;
            mgr.openCamera(chosen,new CameraDevice.StateCallback(){
                @Override public void onOpened(CameraDevice device){
                    camera=device;opening=false;createSession();
                }
                @Override public void onDisconnected(CameraDevice device){
                    device.close();camera=null;fail("Kamera se odpojila");
                }
                @Override public void onError(CameraDevice device,int error){
                    device.close();camera=null;fail("Chyba kamery: "+error);
                }
            },worker);
        }catch(Exception e){fail("Nelze otevřít kameru: "+e.getMessage());}
    }
    private Size chooseRawSize(Size[] sizes) {
        // Prefer 12 MP rather than 50 MP for lower heat/storage.
        Size best=sizes[0];long desired=12_000_000L,bestDiff=Long.MAX_VALUE;
        for(Size size:sizes){
            long px=(long)size.getWidth()*size.getHeight();
            long d=Math.abs(px-desired);
            if(d<bestDiff){bestDiff=d;best=size;}
        }
        return best;
    }
    private Size chooseYuvSize(Size[] sizes){
        Size best=sizes[0];long desired=1280L*720,bestDiff=Long.MAX_VALUE;
        for(Size size:sizes){
            long pixels=(long)size.getWidth()*size.getHeight();
            long diff=Math.abs(pixels-desired);
            if(pixels>1920L*1080)diff+=10_000_000L;
            if(diff<bestDiff){bestDiff=diff;best=size;}
        }
        return best;
    }
    private void createSession(){
        try{
            if(camera==null||reader==null)return;
            camera.createCaptureSession(Collections.singletonList(reader.getSurface()),
                new CameraCaptureSession.StateCallback(){
                    @Override public void onConfigured(CameraCaptureSession s){
                        session=s;
                        try {
                            configureRequest();
                            status="Kalibrace tmavého snímače";
                            report();captureNext();
                        }catch(Exception e){fail("Nastavení kamery selhalo: "+e.getMessage());}
                    }
                    @Override public void onConfigureFailed(CameraCaptureSession s){
                        fail("Kamera odmítla formát "+(raw?"RAW_SENSOR":"YUV"));
                    }
                },worker);
        }catch(Exception e){fail("Nelze spustit kameru: "+e.getMessage());}
    }
    private void configureRequest() throws CameraAccessException {
        requestBuilder=camera.createCaptureRequest(CameraDevice.TEMPLATE_STILL_CAPTURE);
        requestBuilder.addTarget(reader.getSurface());
        int[] caps=characteristics.get(CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES);
        Range<Long> exposureRange=characteristics.get(
            CameraCharacteristics.SENSOR_INFO_EXPOSURE_TIME_RANGE);
        Range<Integer> isoRange=characteristics.get(
            CameraCharacteristics.SENSOR_INFO_SENSITIVITY_RANGE);
        manual=has(caps,CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_MANUAL_SENSOR)
            && exposureRange!=null && isoRange!=null;
        if(manual){
            long desiredNs=(long)Math.max(10,desiredExposureMs)*1_000_000L;
            long ns=Math.max(exposureRange.getLower(),Math.min(desiredNs,exposureRange.getUpper()));
            int iso=Math.max(isoRange.getLower(),Math.min(desiredIso,isoRange.getUpper()));
            requestBuilder.set(CaptureRequest.CONTROL_AE_MODE,CaptureRequest.CONTROL_AE_MODE_OFF);
            requestBuilder.set(CaptureRequest.CONTROL_MODE,CaptureRequest.CONTROL_MODE_OFF);
            requestBuilder.set(CaptureRequest.SENSOR_EXPOSURE_TIME,ns);
            requestBuilder.set(CaptureRequest.SENSOR_SENSITIVITY,iso);
            Long maxFrame=characteristics.get(
                CameraCharacteristics.SENSOR_INFO_MAX_FRAME_DURATION);
            if(maxFrame!=null)
                requestBuilder.set(CaptureRequest.SENSOR_FRAME_DURATION,Math.min(maxFrame,
                    Math.max(ns+10_000_000L,ns)));
            actualExposureNs=ns;actualIso=iso;
        } else {
            actualExposureNs=0;actualIso=0;
            requestBuilder.set(CaptureRequest.CONTROL_AE_MODE,CaptureRequest.CONTROL_AE_MODE_ON);
        }
        if(has(characteristics.get(
            CameraCharacteristics.NOISE_REDUCTION_AVAILABLE_NOISE_REDUCTION_MODES),
            CaptureRequest.NOISE_REDUCTION_MODE_OFF))
            requestBuilder.set(CaptureRequest.NOISE_REDUCTION_MODE,CaptureRequest.NOISE_REDUCTION_MODE_OFF);
        if(has(characteristics.get(
            CameraCharacteristics.HOT_PIXEL_AVAILABLE_HOT_PIXEL_MODES),
            CaptureRequest.HOT_PIXEL_MODE_OFF))
            requestBuilder.set(CaptureRequest.HOT_PIXEL_MODE,CaptureRequest.HOT_PIXEL_MODE_OFF);
        if(has(characteristics.get(CameraCharacteristics.EDGE_AVAILABLE_EDGE_MODES),
            CaptureRequest.EDGE_MODE_OFF))
            requestBuilder.set(CaptureRequest.EDGE_MODE,CaptureRequest.EDGE_MODE_OFF);
        requestBuilder.set(CaptureRequest.CONTROL_AF_MODE,CaptureRequest.CONTROL_AF_MODE_OFF);
        requestBuilder.set(CaptureRequest.FLASH_MODE,CaptureRequest.FLASH_MODE_OFF);
        hardwareInfo=(raw?"RAW 16bit Bayer":"YUV")
            +" · "+captureW+"×"+captureH
            +" · "+(manual?String.format(Locale.US,"%.0f ms",actualExposureNs/1e6):"automatická expozice")
            +" · ISO "+(manual?actualIso:"auto");
    }
    private final CameraCaptureSession.CaptureCallback callback=
        new CameraCaptureSession.CaptureCallback(){
            @Override public void onCaptureCompleted(CameraCaptureSession s,
                    CaptureRequest request,TotalCaptureResult result){
                pendingResult=result;processPairIfReady();
            }
            @Override public void onCaptureFailed(CameraCaptureSession s,
                    CaptureRequest request,CaptureFailure failure){
                if(++consecutiveErrors>=3){fail("Opakované selhání expozice");return;}
                status="Opakuji expozici";report();
                worker.postDelayed(DetectorService.this::captureNext,300);
            }
        };
    private void captureNext(){
        if(camera==null||session==null||requestBuilder==null)return;
        try{
            pendingImage=null;pendingResult=null;
            session.capture(requestBuilder.build(),callback,worker);
        }catch(Exception e){fail("Snímání selhalo: "+e.getMessage());}
    }
    private void processPairIfReady(){
        if(pendingImage==null||pendingResult==null)return;
        Image image=pendingImage;TotalCaptureResult metadata=pendingResult;
        pendingImage=null;pendingResult=null;
        try{
            long imgTs=image.getTimestamp();
            Long resultTs=metadata.get(CaptureResult.SENSOR_TIMESTAMP);
            if(resultTs!=null && Math.abs(imgTs-resultTs)>20_000_000L)
                Log.w("CosmicDetector","Čas snímku a metadat se liší: "+imgTs+" / "+resultTs);
            consecutiveErrors=0;
            processFrame(image,metadata);
        } catch(Exception e){
            Log.e("CosmicDetector","Zpracování snímku selhalo",e);
            status="Chyba snímku: "+e.getMessage();report();
        } finally {
            image.close();
            worker.postDelayed(this::captureNext,60);
        }
    }
    private void processFrame(Image image,TotalCaptureResult meta){
        long now=System.currentTimeMillis();frames++;
        Long exp=meta.get(CaptureResult.SENSOR_EXPOSURE_TIME);
        Integer iso=meta.get(CaptureResult.SENSOR_SENSITIVITY);
        if(exp!=null)actualExposureNs=exp;
        if(iso!=null)actualIso=iso;
        Detector.Analysis analysis;
        byte[] grey=null;
        if(raw)analysis=rawDetector.process(image);
        else {
            grey=readYuv(image);
            analysis=yuvDetector.process(grey,image.getWidth(),image.getHeight(),now);
        }
        boolean ready=raw?rawDetector.ready():yuvDetector.isReady();
        if(!ready){
            status="Kalibrace "+(raw?rawDetector.calibrated():yuvDetector.calibratedFrames())
                +"/"+(raw?RawDetector.CALIBRATION_FRAMES:Detector.CALIBRATION_FRAMES);
        } else if(analysis.lightLeak) {
            status="Podezřele světlý snímek – zkontroluj zakrytí objektivu";
        } else status="Měřím · "+(raw?"RAW":"YUV");
        String dng="";
        if(raw && ready && !analysis.hits.isEmpty() && saveDng && dngCount<50){
            dng=writeDng(image,meta,now);
        }
        for(Detector.Hit hit:analysis.hits){
            byte[] patch=raw?rawDetector.differencePatch(hit.x,hit.y,96)
                :extractYuvPatch(grey,image.getWidth(),image.getHeight(),hit.x,hit.y);
            String png=savePng(patch,96,now,events);
            db.add(now,hit.x,hit.y,hit.pixels,hit.peak,png,
                raw?"RAW_SENSOR":"YUV_420_888",actualExposureNs,actualIso,dng);
            events++;
        }
        if(now-lastReport>800 || !analysis.hits.isEmpty()){
            lastReport=now;report();
        }
    }
    private byte[] readYuv(Image image) {
        int w=image.getWidth(),h=image.getHeight();
        byte[] result=new byte[w*h];
        Image.Plane plane=image.getPlanes()[0];
        ByteBuffer buffer=plane.getBuffer();
        int stride=plane.getRowStride(),step=plane.getPixelStride();
        for(int y=0;y<h;y++)for(int x=0;x<w;x++)
            result[y*w+x]=buffer.get(y*stride+x*step);
        return result;
    }
    private byte[] extractYuvPatch(byte[] grey,int w,int h,int x,int y){
        byte[] patch=new byte[96*96];
        for(int py=0;py<96;py++)for(int px=0;px<96;px++){
            int xx=x+px-48,yy=y+py-48;
            if(xx>=0 && xx<w && yy>=0 && yy<h){
                int value=(grey[yy*w+xx]&255);
                patch[py*96+px]=(byte)Math.min(255,value*2);
            }
        }
        return patch;
    }
    private String savePng(byte[] grey,int size,long now,int serial){
        Bitmap bmp=null;
        try{
            int[] rgba=new int[size*size];
            for(int i=0;i<rgba.length;i++){
                int p=grey[i]&255;rgba[i]=Color.rgb(p,p,p);
            }
            bmp=Bitmap.createBitmap(rgba,size,size,Bitmap.Config.ARGB_8888);
            File dir=new File(getFilesDir(),"captures");
            if(!dir.exists() && !dir.mkdirs())return "";
            String name=now+"-"+serial+".png";
            try(FileOutputStream out=new FileOutputStream(new File(dir,name))){
                bmp.compress(Bitmap.CompressFormat.PNG,100,out);
            }
            return name;
        }catch(Exception e){Log.w("CosmicDetector","Uložení výřezu",e);return "";}
        finally{if(bmp!=null)bmp.recycle();}
    }
    private String writeDng(Image image,TotalCaptureResult meta,long now){
        File file=null;
        try{
            File dir=new File(getFilesDir(),"captures");
            if(!dir.exists() && !dir.mkdirs())return "";
            String name=now+"-"+frames+".dng";
            file=new File(dir,name);
            try(DngCreator writer=new DngCreator(characteristics,meta);
                FileOutputStream out=new FileOutputStream(file)){
                writer.writeImage(out,image);
            }
            dngCount++;return name;
        }catch(Exception e){
            Log.w("CosmicDetector","Uložení DNG",e);
            if(file!=null)file.delete();
            return "";
        }
    }
    private void report(){
        int cal=raw?rawDetector.calibrated():yuvDetector.calibratedFrames();
        int rejected=raw?rawDetector.rejected():yuvDetector.getBadFrames();
        prefs.edit()
            .putBoolean("running",camera!=null||opening||(startTime>0))
            .putString("status",status)
            .putString("mode",raw?"RAW_SENSOR":"YUV")
            .putString("cameraInfo",hardwareInfo)
            .putLong("start",startTime)
            .putInt("frames",frames).putInt("calibration",cal)
            .putInt("calibrationTarget",raw?RawDetector.CALIBRATION_FRAMES:Detector.CALIBRATION_FRAMES)
            .putInt("rejected",rejected).putInt("events",events)
            .putInt("width",captureW).putInt("height",captureH)
            .putLong("actualExposureNs",actualExposureNs)
            .putInt("actualIso",actualIso).putBoolean("rawMode",raw)
            .putInt("dngCount",dngCount).apply();
    }
    @Override public void onDestroy(){
        try{if(session!=null){session.stopRepeating();session.close();}}catch(Exception ignored){}
        try{if(pendingImage!=null)pendingImage.close();}catch(Exception ignored){}
        if(reader!=null)reader.close();
        try{if(camera!=null)camera.close();}catch(Exception ignored){}
        if(wakeLock!=null&&wakeLock.isHeld())wakeLock.release();
        prefs.edit().putBoolean("running",false).putString("status","Zastaveno").apply();
        if(thread!=null)thread.quitSafely();
        if(db!=null)db.close();
        super.onDestroy();
    }
    @Override public IBinder onBind(Intent intent){return null;}
}
