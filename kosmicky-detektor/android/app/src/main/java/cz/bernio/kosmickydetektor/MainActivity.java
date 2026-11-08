package cz.bernio.kosmickydetektor;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.widget.*;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.io.File;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;

public final class MainActivity extends Activity {
    private static final int COLOR_BG=0xff08121e,COLOR_PANEL=0xff142538,
        COLOR_TEXT=0xfff0f7ff,COLOR_MUTED=0xffa7bac9,COLOR_ACCENT=0xff66e8be;
    private static final int PERMISSION_REQUEST=102;
    private static final int EXPORT_REQUEST=103;
    private final Handler ui=new Handler(Looper.getMainLooper());
    private EventStore db;
    private SharedPreferences prefs;
    private TextView status,stats,settingsLabel,history;
    private ImageView preview;
    private Button startButton,stopButton;
    private SeekBar thresholdSlider;
    private int threshold=65;
    private final Runnable updater=new Runnable() {
        @Override public void run() {refresh();ui.postDelayed(this,1200);}
    };

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(COLOR_BG);
        getWindow().setNavigationBarColor(COLOR_BG);
        db=new EventStore(this);
        prefs=getSharedPreferences(DetectorService.PREFS,MODE_PRIVATE);
        threshold=prefs.getInt("threshold",65);
        buildUi();
        refresh();
    }
    private int dp(float n) {return (int)(n*getResources().getDisplayMetrics().density+0.5f);}
    private GradientDrawable background(int color,int radius) {
        GradientDrawable b=new GradientDrawable();
        b.setColor(color);b.setCornerRadius(dp(radius));
        return b;
    }
    private TextView text(String value,int size,int color,boolean bold) {
        TextView t=new TextView(this);
        t.setText(value);t.setTextSize(size);t.setTextColor(color);
        if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        t.setLineSpacing(dp(2),1f);
        return t;
    }
    private LinearLayout vertical() {
        LinearLayout ll=new LinearLayout(this);
        ll.setOrientation(LinearLayout.VERTICAL);
        return ll;
    }
    private LinearLayout card(LinearLayout root) {
        LinearLayout c=vertical();
        c.setPadding(dp(16),dp(16),dp(16),dp(16));
        c.setBackground(background(COLOR_PANEL,18));
        LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,LinearLayout.LayoutParams.WRAP_CONTENT);
        params.bottomMargin=dp(14);root.addView(c,params);
        return c;
    }
    private void spaced(LinearLayout box,View v,int after) {
        LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,LinearLayout.LayoutParams.WRAP_CONTENT);
        p.bottomMargin=dp(after);box.addView(v,p);
    }
    private Button action(String label,int bg,int fg) {
        Button b=new Button(this);
        b.setAllCaps(false);b.setText(label);b.setTextSize(15);
        b.setTextColor(fg);b.setBackground(background(bg,12));
        b.setPadding(dp(10),dp(7),dp(10),dp(7));
        return b;
    }
    private void buildUi() {
        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);
        scroll.setBackgroundColor(COLOR_BG);
        LinearLayout root=vertical();
        root.setPadding(dp(16),dp(22),dp(16),dp(24));
        scroll.addView(root);
        setContentView(scroll);
        spaced(root,text("☄  KOSMICKÝ DETEKTOR",13,COLOR_ACCENT,true),8);
        spaced(root,text("Měření částic fotoaparátem",24,COLOR_TEXT,true),8);
        spaced(root,text("Nativní Camera2 · bez PWA · experimentální detekce",13,COLOR_MUTED,false),20);

        LinearLayout panel=card(root);
        spaced(panel,text("STAV DETEKTORU",12,COLOR_MUTED,true),8);
        status=text("Připraveno",17,COLOR_ACCENT,true);
        spaced(panel,status,10);
        stats=text("Zatím žádné měření",15,COLOR_TEXT,false);
        spaced(panel,stats,16);
        LinearLayout buttons=new LinearLayout(this);
        buttons.setOrientation(LinearLayout.HORIZONTAL);
        startButton=action("▶ Spustit",0xff18775e,COLOR_TEXT);
        stopButton=action("■ Zastavit",0xff503344,COLOR_TEXT);
        LinearLayout.LayoutParams b1=new LinearLayout.LayoutParams(0,dp(50),1);
        b1.rightMargin=dp(8);
        buttons.addView(startButton,b1);
        buttons.addView(stopButton,new LinearLayout.LayoutParams(0,dp(50),1));
        spaced(panel,buttons,10);
        Button calibrate=action("Znovu kalibrovat tmavý obraz",0xff273e51,COLOR_TEXT);
        spaced(panel,calibrate,0);
        startButton.setOnClickListener(v->askStart());
        stopButton.setOnClickListener(v->send(DetectorService.STOP));
        calibrate.setOnClickListener(v->send(DetectorService.RECALIBRATE));

        LinearLayout settingsPanel=card(root);
        spaced(settingsPanel,text("CITLIVOST",12,COLOR_MUTED,true),8);
        settingsLabel=text("",15,COLOR_TEXT,false);
        spaced(settingsPanel,settingsLabel,4);
        thresholdSlider=new SeekBar(this);
        thresholdSlider.setMax(150);thresholdSlider.setProgress(threshold-30);
        spaced(settingsPanel,thresholdSlider,4);
        settingsLabel.setText("Práh: "+threshold+" / 255 · nižší = více kandidátů");
        thresholdSlider.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override public void onProgressChanged(SeekBar bar,int progress,boolean fromUser) {
                threshold=30+progress;
                settingsLabel.setText("Práh: "+threshold+" / 255 · nižší = více kandidátů");
                if(fromUser)prefs.edit().putInt("threshold",threshold).apply();
            }
            @Override public void onStartTrackingTouch(SeekBar bar){}
            @Override public void onStopTrackingTouch(SeekBar bar){}
        });
        spaced(settingsPanel,text("Nastavení prahu platí od příštího spuštění. Po startu zakryj objektiv a nech proběhnout kalibraci (50 snímků).",12,COLOR_MUTED,false),0);

        LinearLayout hitsPanel=card(root);
        spaced(hitsPanel,text("ZACHYCENÉ UDÁLOSTI",12,COLOR_MUTED,true),8);
        history=text("Zatím žádné kandidátní zásahy.",14,COLOR_TEXT,false);
        spaced(hitsPanel,history,10);
        preview=new ImageView(this);
        preview.setAdjustViewBounds(true);
        preview.setScaleType(ImageView.ScaleType.FIT_CENTER);
        preview.setBackground(background(0xff05090d,8));
        LinearLayout.LayoutParams ip=new LinearLayout.LayoutParams(dp(192),dp(192));
        ip.gravity=Gravity.CENTER_HORIZONTAL;ip.bottomMargin=dp(14);
        hitsPanel.addView(preview,ip);
        Button export=action("Uložit výsledky jako CSV",0xff273e51,COLOR_TEXT);
        spaced(hitsPanel,export,0);
        export.setOnClickListener(v->exportCsv());

        LinearLayout guide=card(root);
        spaced(guide,text("JAK MĚŘIT",12,COLOR_MUTED,true),8);
        spaced(guide,text("1. Neprůsvitně zakryj zadní fotoaparát.\n2. Spusť měření a vyčkej na kalibraci.\n3. Nech přístroj v klidu měřit. Kamera běží v popředí se systémovou notifikací.\n4. Podezřelé události můžeš exportovat do CSV.",14,COLOR_TEXT,false),12);
        spaced(guide,text("Pozor: jasný bod není důkaz kosmické částice. Může jít o šum, vadný pixel nebo obrazový artefakt. Android ani výrobce nezaručuje dlouhý provoz kamery po zamknutí.",12,COLOR_MUTED,false),0);
    }
    private void askStart() {
        if(checkSelfPermission(Manifest.permission.CAMERA)!=PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.CAMERA},PERMISSION_REQUEST);
            return;
        }
        startMeasurement();
    }
    private void startMeasurement() {
        if(prefs.getBoolean("running",false))return;
        Intent intent=new Intent(this,DetectorService.class).setAction(DetectorService.START);
        intent.putExtra("threshold",threshold);
        try {startForegroundService(intent);}
        catch(Exception e) {
            new AlertDialog.Builder(this).setMessage("Nepodařilo se spustit měření: "+e.getMessage())
                .setPositiveButton("OK",null).show();
        }
        if(Build.VERSION.SDK_INT>=33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)
            !=PackageManager.PERMISSION_GRANTED)
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},104);
        ui.postDelayed(this::refresh,400);
    }
    @Override public void onRequestPermissionsResult(int requestCode,String[] permissions,int[] grants) {
        super.onRequestPermissionsResult(requestCode,permissions,grants);
        if(requestCode==PERMISSION_REQUEST) {
            if(grants.length>0 && grants[0]==PackageManager.PERMISSION_GRANTED)startMeasurement();
            else Toast.makeText(this,"Pro měření je nutné povolit fotoaparát.",Toast.LENGTH_LONG).show();
        }
    }
    private void send(String action) {
        if(!prefs.getBoolean("running",false))return;
        try {startService(new Intent(this,DetectorService.class).setAction(action));}
        catch(Exception e) {Toast.makeText(this,"Nelze ovládat měření: "+e.getMessage(),Toast.LENGTH_LONG).show();}
        ui.postDelayed(this::refresh,500);
    }
    private void exportCsv() {
        Intent intent=new Intent(Intent.ACTION_CREATE_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("text/csv");
        intent.putExtra(Intent.EXTRA_TITLE,"kosmicky-detektor-"+System.currentTimeMillis()+".csv");
        startActivityForResult(intent,EXPORT_REQUEST);
    }
    @Override protected void onActivityResult(int requestCode,int resultCode,Intent data) {
        super.onActivityResult(requestCode,resultCode,data);
        if(requestCode==EXPORT_REQUEST && resultCode==RESULT_OK && data!=null && data.getData()!=null) {
            try(OutputStream out=getContentResolver().openOutputStream(data.getData())) {
                if(out==null)throw new IllegalStateException("Není k dispozici výstupní soubor");
                out.write(db.exportCsv().getBytes(StandardCharsets.UTF_8));
                Toast.makeText(this,"CSV uloženo.",Toast.LENGTH_LONG).show();
            } catch(Exception e) {
                Toast.makeText(this,"Export se nezdařil: "+e.getMessage(),Toast.LENGTH_LONG).show();
            }
        }
    }
    private void refresh() {
        if(status==null)return;
        boolean running=prefs.getBoolean("running",false);
        String detail=prefs.getString("status","Připraveno");
        status.setText(running ? "● "+detail : detail);
        status.setTextColor(running?COLOR_ACCENT:COLOR_MUTED);
        startButton.setEnabled(!running);
        stopButton.setEnabled(running);
        int frames=prefs.getInt("frames",0);
        int candidateCount=prefs.getInt("events",0);
        int cal=prefs.getInt("calibration",0);
        int rejected=prefs.getInt("rejected",0);
        int w=prefs.getInt("width",0),h=prefs.getInt("height",0);
        long start=prefs.getLong("start",0);
        String duration="—";
        if(start>0) {
            long secs=Math.max(0,(System.currentTimeMillis()-start)/1000);
            duration=(secs/3600)+" h "+((secs/60)%60)+" min "+(secs%60)+" s";
        }
        stats.setText("Kandidátní zásahy: "+candidateCount+"   •   celkem uloženo: "+db.count()+
            "\nSnímky: "+frames+"   •   kalibrace: "+cal+"/50"+
            "\nNadměrně světlé snímky: "+rejected+
            "\nRozlišení: "+(w>0?w+" × "+h:"—")+"   •   délka běhu: "+duration);
        List<EventStore.EventRow> rows=db.latest(5);
        if(rows.isEmpty()) {
            history.setText("Zatím žádné kandidátní zásahy.");
            preview.setImageDrawable(null);
            return;
        }
        SimpleDateFormat format=new SimpleDateFormat("d. M. HH:mm:ss",Locale.forLanguageTag("cs-CZ"));
        StringBuilder items=new StringBuilder();
        for(EventStore.EventRow row:rows) {
            items.append(format.format(new Date(row.time)))
                .append("  ·  ").append(row.pixels).append(" px")
                .append("  ·  Δ ").append(row.peak).append("\n");
        }
        history.setText(items.toString().trim());
        EventStore.EventRow first=rows.get(0);
        if(first.picture!=null && !first.picture.isEmpty()) {
            File img=new File(new File(getFilesDir(),"captures"),first.picture);
            preview.setImageBitmap(BitmapFactory.decodeFile(img.getAbsolutePath()));
        }
    }
    @Override protected void onResume() {super.onResume();ui.removeCallbacks(updater);ui.post(updater);}
    @Override protected void onPause() {ui.removeCallbacks(updater);super.onPause();}
    @Override protected void onDestroy() {db.close();super.onDestroy();}
}
