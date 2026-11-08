package cz.bernio.kosmickydetektor;

import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import android.content.ContentValues;
import java.util.ArrayList;
import java.util.List;
import java.util.HashSet;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;
import java.io.OutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

public final class EventStore extends SQLiteOpenHelper {
    public static final class EventRow {
        public final long id, time;
        public final int x, y, pixels, peak;
        public final String picture;
        public final String mode,dngFile;
        public final long exposureNs;
        public final int iso;
        EventRow(long id, long time, int x, int y, int pixels, int peak, String picture, String mode, long exposureNs, int iso, String dngFile) {
            this.id = id; this.time = time; this.x = x; this.y = y;
            this.pixels = pixels; this.peak = peak; this.picture = picture;
            this.mode=mode; this.exposureNs=exposureNs; this.iso=iso; this.dngFile=dngFile;
        }
    }

    public EventStore(Context context) { super(context, "cosmic_events.db", null, 2); }
    @Override public void onCreate(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE events(_id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER NOT NULL, x INTEGER, y INTEGER, px INTEGER, peak INTEGER, picture TEXT, mode TEXT, exposure_ns INTEGER, iso INTEGER, dng_file TEXT)");
        db.execSQL("CREATE INDEX events_ts ON events(ts)");
    }
    @Override public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
        if(oldVersion<2){
            db.execSQL("ALTER TABLE events ADD COLUMN mode TEXT");
            db.execSQL("ALTER TABLE events ADD COLUMN exposure_ns INTEGER");
            db.execSQL("ALTER TABLE events ADD COLUMN iso INTEGER");
            db.execSQL("ALTER TABLE events ADD COLUMN dng_file TEXT");
        }
    }

    public synchronized void add(long ts, int x, int y, int px, int peak, String picture,
        String mode, long exposureNs, int iso, String dngFile) {
        ContentValues values = new ContentValues();
        values.put("ts", ts); values.put("x", x); values.put("y", y);
        values.put("px", px); values.put("peak", peak); values.put("picture", picture);
        values.put("mode", mode); values.put("exposure_ns",exposureNs);
        values.put("iso",iso);values.put("dng_file",dngFile);
        getWritableDatabase().insert("events", null, values);
    }
    public synchronized long count() {
        try (Cursor c = getReadableDatabase().rawQuery("SELECT COUNT(*) FROM events", null)) {
            return c.moveToFirst() ? c.getLong(0) : 0;
        }
    }
    public synchronized List<EventRow> latest(int limit) {
        ArrayList<EventRow> rows = new ArrayList<>();
        try (Cursor c = getReadableDatabase().rawQuery(
                "SELECT _id,ts,x,y,px,peak,picture,mode,exposure_ns,iso,dng_file FROM events ORDER BY _id DESC LIMIT " + Math.max(1, Math.min(100, limit)), null)) {
            while (c.moveToNext()) {
                rows.add(new EventRow(c.getLong(0),c.getLong(1),c.getInt(2),
                    c.getInt(3),c.getInt(4),c.getInt(5),c.getString(6),
                    c.getString(7),c.getLong(8),c.getInt(9),c.getString(10)));
            }
        }
        return rows;
    }
    public synchronized String exportCsv() {
        StringBuilder csv = new StringBuilder("id,unix_ms,x,y,pixels,peak_delta,preview_file,mode,exposure_ns,iso,dng_file\n");
        try (Cursor c = getReadableDatabase().rawQuery(
                "SELECT _id,ts,x,y,px,peak,picture,mode,exposure_ns,iso,dng_file FROM events ORDER BY _id ASC", null)) {
            while (c.moveToNext()) {
                csv.append(c.getLong(0)).append(',').append(c.getLong(1)).append(',')
                   .append(c.getInt(2)).append(',').append(c.getInt(3)).append(',')
                   .append(c.getInt(4)).append(',').append(c.getInt(5)).append(',');
                String name = c.getString(6);
                if (name != null) csv.append('"').append(name.replace("\"","\"\"")).append('"');
                csv.append(',').append(c.getString(7)==null?"":c.getString(7))
                    .append(',').append(c.getLong(8)).append(',').append(c.getInt(9)).append(',');
                String dng=c.getString(10);
                if(dng!=null)csv.append('"').append(dng.replace("\"","\"\"")).append('"');
                csv.append('\n');
            }
        }
        return csv.toString();
    }

    public synchronized void writeZip(OutputStream output,File baseDir) throws IOException {
        HashSet<String> seen=new HashSet<>();
        try(ZipOutputStream zip=new ZipOutputStream(output)){
            zip.putNextEntry(new ZipEntry("measurements.csv"));
            zip.write(exportCsv().getBytes(StandardCharsets.UTF_8));
            zip.closeEntry();
            try(Cursor c=getReadableDatabase().rawQuery(
                "SELECT picture,dng_file FROM events ORDER BY _id ASC",null)){
                while(c.moveToNext()){
                    for(int n=0;n<2;n++){
                        String name=c.getString(n);
                        if(name==null||name.isEmpty()||!seen.add(name))continue;
                        // Only application-generated flat basenames; no traversal or extraction.
                        if(name.contains("/")||name.contains("\\")||name.contains(".."))continue;
                        File source=new File(baseDir,name);
                        if(!source.isFile())continue;
                        zip.putNextEntry(new ZipEntry("captures/"+name));
                        try(FileInputStream in=new FileInputStream(source)){
                            byte[] buffer=new byte[65536];int read;
                            while((read=in.read(buffer))!=-1)zip.write(buffer,0,read);
                        }
                        zip.closeEntry();
                    }
                }
            }
        }
    }
}
