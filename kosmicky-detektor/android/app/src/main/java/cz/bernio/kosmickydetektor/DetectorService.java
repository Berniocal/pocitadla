package cz.bernio.kosmickydetektor;

import android.Manifest;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
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
import android.os.Build;
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
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

public final class DetectorService extends Service {
    public static final String START="cz.bernio.kosmickydetektor.START";
    public static final String STOP="cz.bernio.kosmickydetektor.STOP";
    public static final String RECALIBRATE="cz.bernio.kosmickydetektor.RECALIBRATE";
    public static final String PREFS="detector_state";
    private static final int NOTIFICATION_ID=42;
    private final Detector detector=new Detector();
    private HandlerThread thread;
    private Handler worker;
    private CameraDevice camera;
    private CameraCaptureSession session;
    private ImageReader reader;
    private EventStore db;
    private PowerManager.WakeLock wakeLock;
    private SharedPreferences prefs;
    private boolean opening=false;
    private int captureW=0,captureH=0,sensitivity=65;
    private long startTime=0,lastReport=0;
    private int events=0;
    private byte[] frame=null;
    private String status="Připraveno";

    @Override public void onCreate() {
        super.onCreate();
        prefs=getSharedPreferences(PREFS,MODE_PRIVATE);
        db=new EventStore(this);
        thread=new HandlerThread("Cosmic-Camera2");
        thread.start();
        worker=new Handler(thread.getLooper());
        NotificationManager nm=(NotificationManager)getSystemService(NOTIFICATION_SERVICE);
        nm.createNotificationChannel(new NotificationChannel("cosmic_measure","Kosmické měření",NotificationManager.IMPORTANCE_LOW));
    }

    @Override public int onStartCommand(Intent intent,int flags,int startId) {
        if(intent!=null && STOP.equals(intent.getAction())) {
            stopSelf();return START_NOT_STICKY;
        }
        if(intent!=null && RECALIBRATE.equals(intent.getAction())) {
            worker.post(()->{detector.reset();status="Nová kalibrace";report();});
            return START_NOT_STICKY;
        }
        if(camera!=null || opening)return START_NOT_STICKY;
        sensitivity=intent!=null?intent.getIntExtra("threshold",65):65;
        detector.setThreshold(sensitivity);
        startTime=System.currentTimeMillis();events=0;status="Otevírám kameru";
        startForeground(NOTIFICATION_ID,notifyText("Kalibrace a měření"),
            ServiceInfo.FOREGROUND_SERVICE_TYPE_CAMERA);
        PowerManager pm=(PowerManager)getSystemService(POWER_SERVICE);
        wakeLock=pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK,"CosmicDetector:CameraMeasurement");
        wakeLock.acquire();
        report();
        worker.post(this::openCamera);
        return START_NOT_STICKY;
    }

    private Notification notifyText(String text) {
        Intent i=new Intent(this,MainActivity.class);
        android.app.PendingIntent click=android.app.PendingIntent.getActivity(
            this,0,i,android.app.PendingIntent.FLAG_IMMUTABLE | android.app.PendingIntent.FLAG_UPDATE_CURRENT);
        Intent stop=new Intent(this,DetectorService.class); stop.setAction(STOP);
        android.app.PendingIntent stopClick=android.app.PendingIntent.getService(
            this,1,stop,android.app.PendingIntent.FLAG_IMMUTABLE | android.app.PendingIntent.FLAG_UPDATE_CURRENT);
        return new Notification.Builder(this,"cosmic_measure")
            .setContentTitle("Kosmický detektor")
            .setContentText(text)
            .setSmallIcon(android.R.drawable.ic_menu_camera)
            .setOngoing(true)
            .setContentIntent(click)
            .addAction(new Notification.Action.Builder(android.R.drawable.ic_media_pause,"Zastavit",stopClick).build())
            .build();
    }

    private void fail(String reason) {
        status=reason;
        report();
        Log.e("CosmicDetector",reason);
        if(worker!=null)worker.postDelayed(this::stopSelf,1000);
    }

    private void openCamera() {
        try {
            if(checkSelfPermission(Manifest.permission.CAMERA)!=PackageManager.PERMISSION_GRANTED) {
                fail("Chybí oprávnění fotoaparátu");return;
            }
            CameraManager mgr=(CameraManager)getSystemService(Context.CAMERA_SERVICE);
            String chosen=null;
            CameraCharacteristics chars=null;
            for(String id:mgr.getCameraIdList()) {
                CameraCharacteristics c=mgr.getCameraCharacteristics(id);
                Integer facing=c.get(CameraCharacteristics.LENS_FACING);
                if(facing!=null && facing==CameraCharacteristics.LENS_FACING_BACK) {
                    StreamConfigurationMap map=c.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
                    if(map!=null && map.getOutputSizes(ImageFormat.YUV_420_888)!=null) {
                        chosen=id;chars=c;break;
                    }
                }
            }
            if(chosen==null || chars==null) {fail("Nenalezena vhodná zadní kamera");return;}
            StreamConfigurationMap map=chars.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
            Size selected=chooseSize(map.getOutputSizes(ImageFormat.YUV_420_888));
            captureW=selected.getWidth();captureH=selected.getHeight();
            reader=ImageReader.newInstance(captureW,captureH,ImageFormat.YUV_420_888,3);
            reader.setOnImageAvailableListener(onImage,worker);
            final CameraCharacteristics chosenChars=chars;
            opening=true;
            mgr.openCamera(chosen,new CameraDevice.StateCallback() {
                @Override public void onOpened(CameraDevice device) {
                    opening=false;camera=device;createSession(chosenChars);
                }
                @Override public void onDisconnected(CameraDevice device) {
                    device.close();camera=null;fail("Kamera odpojena");
                }
                @Override public void onError(CameraDevice device,int error) {
                    device.close();camera=null;fail("Chyba kamery "+error);
                }
            },worker);
        } catch(Exception e) {fail("Nelze otevřít kameru: "+e.getMessage());}
    }

    private Size chooseSize(Size[] sizes) {
        if(sizes==null || sizes.length==0)return new Size(640,480);
        Size best=sizes[0];long score=Long.MAX_VALUE;
        for(Size s:sizes) {
            long a=(long)s.getWidth()*s.getHeight();
            long val=Math.abs(a-640L*480L);
            if(a<320L*240L)val+=10000000L;
            if(a>1280L*720L)val+=10000000L;
            if(val<score){score=val;best=s;}
        }
        return best;
    }

    private static boolean supports(int[] modes,int desired) {
        if(modes==null)return false;
        for(int mode:modes)if(mode==desired)return true;
        return false;
    }

    private void createSession(CameraCharacteristics cc) {
        if(camera==null || reader==null)return;
        try {
            camera.createCaptureSession(Collections.singletonList(reader.getSurface()),
                new CameraCaptureSession.StateCallback() {
                    @Override public void onConfigured(CameraCaptureSession s) {
                        session=s;
                        try {
                            CaptureRequest.Builder request=camera.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW);
                            request.addTarget(reader.getSurface());
                            int[] caps=cc.get(CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES);
                            boolean manual=supports(caps, CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_MANUAL_SENSOR);
                            Range<Long> exp=cc.get(CameraCharacteristics.SENSOR_INFO_EXPOSURE_TIME_RANGE);
                            Range<Integer> iso=cc.get(CameraCharacteristics.SENSOR_INFO_SENSITIVITY_RANGE);
                            if(manual && exp!=null && iso!=null) {
                                long requested=100000000L;
                                long exposure=Math.max(exp.getLower(),Math.min(requested,exp.getUpper()));
                                request.set(CaptureRequest.CONTROL_AE_MODE,CaptureRequest.CONTROL_AE_MODE_OFF);
                                request.set(CaptureRequest.SENSOR_EXPOSURE_TIME,exposure);
                                request.set(CaptureRequest.SENSOR_SENSITIVITY,
                                    Math.max(iso.getLower(),Math.min(iso.getUpper(),800)));
                                status="Ruční expozice "+(exposure/1000000)+" ms";
                            } else status="Automatická expozice (hardware nepovoluje manuální)";
                            if(supports(cc.get(CameraCharacteristics.NOISE_REDUCTION_AVAILABLE_NOISE_REDUCTION_MODES),
                                    CaptureRequest.NOISE_REDUCTION_MODE_OFF))
                                request.set(CaptureRequest.NOISE_REDUCTION_MODE,CaptureRequest.NOISE_REDUCTION_MODE_OFF);
                            if(supports(cc.get(CameraCharacteristics.HOT_PIXEL_AVAILABLE_HOT_PIXEL_MODES),
                                    CaptureRequest.HOT_PIXEL_MODE_OFF))
                                request.set(CaptureRequest.HOT_PIXEL_MODE,CaptureRequest.HOT_PIXEL_MODE_OFF);
                            if(supports(cc.get(CameraCharacteristics.EDGE_AVAILABLE_EDGE_MODES),
                                    CaptureRequest.EDGE_MODE_OFF))
                                request.set(CaptureRequest.EDGE_MODE,CaptureRequest.EDGE_MODE_OFF);
                            request.set(CaptureRequest.CONTROL_AF_MODE,CaptureRequest.CONTROL_AF_MODE_OFF);
                            session.setRepeatingRequest(request.build(),null,worker);
                            report();
                        } catch(Exception e) {fail("Nelze nastavit snímání: "+e.getMessage());}
                    }
                    @Override public void onConfigureFailed(CameraCaptureSession s) {fail("Nastavení kamery selhalo");}
                },worker);
        } catch(Exception e) {fail("Nelze spustit snímání: "+e.getMessage());}
    }

    private final ImageReader.OnImageAvailableListener onImage = src -> {
        try (Image image=src.acquireLatestImage()) {
            if(image==null)return;
            int w=image.getWidth(),h=image.getHeight();
            if(frame==null || frame.length!=w*h)frame=new byte[w*h];
            Image.Plane plane=image.getPlanes()[0];
            ByteBuffer buffer=plane.getBuffer();
            int stride=plane.getRowStride(),pixelStride=plane.getPixelStride();
            if(pixelStride==1 && stride==w) {
                buffer.position(0);buffer.get(frame,0,frame.length);
            } else {
                for(int y=0;y<h;y++) for(int x=0;x<w;x++) {
                    frame[y*w+x]=buffer.get(y*stride+x*pixelStride);
                }
            }
            long now=System.currentTimeMillis();
            Detector.Analysis result=detector.process(frame,w,h,now);
            if(!detector.isReady()) status="Kalibrace "+detector.calibratedFrames()+"/"+Detector.CALIBRATION_FRAMES;
            else if(result.lightLeak)status="Příliš světlý snímek – zkontroluj zakrytí objektivu";
            else status="Měřím (kamera "+w+"×"+h+")";
            for(Detector.Hit hit:result.hits) {
                String picture=saveCrop(frame,w,h,hit.x,hit.y,now,events);
                db.add(now,hit.x,hit.y,hit.pixels,hit.peak,picture);
                events++;
            }
            if(now-lastReport>1200) {
                lastReport=now;
                report();
            }
        } catch(Exception e) {Log.e("CosmicDetector","Analýza snímku",e);}
    };

    private String saveCrop(byte[] grey,int w,int h,int x,int y,long now,int serial) {
        Bitmap bmp=null;
        try {
            int size=96;int[] argb=new int[size*size];
            for(int py=0;py<size;py++)for(int px=0;px<size;px++) {
                int sx=x+px-size/2,sy=y+py-size/2;
                int brightness=0;
                if(sx>=0 && sy>=0 && sx<w && sy<h)
                    brightness=(grey[sy*w+sx]&255);
                brightness=Math.min(255,brightness*2);
                argb[py*size+px]=Color.rgb(brightness,brightness,brightness);
            }
            bmp=Bitmap.createBitmap(argb,size,size,Bitmap.Config.ARGB_8888);
            File folder=new File(getFilesDir(),"captures");
            if(!folder.exists() && !folder.mkdirs())return "";
            String filename=now+"-"+serial+".png";
            try(FileOutputStream out=new FileOutputStream(new File(folder,filename))) {
                bmp.compress(Bitmap.CompressFormat.PNG,100,out);
            }
            return filename;
        } catch(Exception e) {
            Log.w("CosmicDetector","Není možné uložit výřez",e);
            return "";
        } finally {if(bmp!=null)bmp.recycle();}
    }

    private void report() {
        prefs.edit().putBoolean("running",camera!=null || opening || (startTime>0))
            .putString("status",status)
            .putLong("start",startTime)
            .putInt("frames",detector.getFrames())
            .putInt("calibration",detector.calibratedFrames())
            .putInt("rejected",detector.getBadFrames())
            .putInt("events",events)
            .putInt("width",captureW).putInt("height",captureH)
            .apply();
    }
    @Override public void onDestroy() {
        try {if(session!=null){session.stopRepeating();session.close();}}catch(Exception ignored){}
        try {if(camera!=null)camera.close();}catch(Exception ignored){}
        if(reader!=null)reader.close();
        if(wakeLock!=null && wakeLock.isHeld())wakeLock.release();
        prefs.edit().putBoolean("running",false).putString("status","Zastaveno").apply();
        if(thread!=null)thread.quitSafely();
        if(db!=null)db.close();
        super.onDestroy();
    }
    @Override public IBinder onBind(Intent intent) {return null;}
}
