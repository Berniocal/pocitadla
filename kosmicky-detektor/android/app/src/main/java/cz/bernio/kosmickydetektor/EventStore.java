package cz.bernio.kosmickydetektor;

import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import android.content.ContentValues;
import java.util.ArrayList;
import java.util.List;

public final class EventStore extends SQLiteOpenHelper {
    public static final class EventRow {
        public final long id, time;
        public final int x, y, pixels, peak;
        public final String picture;
        EventRow(long id, long time, int x, int y, int pixels, int peak, String picture) {
            this.id = id; this.time = time; this.x = x; this.y = y;
            this.pixels = pixels; this.peak = peak; this.picture = picture;
        }
    }

    public EventStore(Context context) { super(context, "cosmic_events.db", null, 1); }
    @Override public void onCreate(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE events(_id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER NOT NULL, x INTEGER, y INTEGER, px INTEGER, peak INTEGER, picture TEXT)");
        db.execSQL("CREATE INDEX events_ts ON events(ts)");
    }
    @Override public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) { }

    public synchronized void add(long ts, int x, int y, int px, int peak, String picture) {
        ContentValues values = new ContentValues();
        values.put("ts", ts); values.put("x", x); values.put("y", y);
        values.put("px", px); values.put("peak", peak); values.put("picture", picture);
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
                "SELECT _id,ts,x,y,px,peak,picture FROM events ORDER BY _id DESC LIMIT " + Math.max(1, Math.min(100, limit)), null)) {
            while (c.moveToNext()) {
                rows.add(new EventRow(c.getLong(0),c.getLong(1),c.getInt(2),
                    c.getInt(3),c.getInt(4),c.getInt(5),c.getString(6)));
            }
        }
        return rows;
    }
    public synchronized String exportCsv() {
        StringBuilder csv = new StringBuilder("id,unix_ms,x,y,pixels,peak_delta,preview_file\n");
        try (Cursor c = getReadableDatabase().rawQuery(
                "SELECT _id,ts,x,y,px,peak,picture FROM events ORDER BY _id ASC", null)) {
            while (c.moveToNext()) {
                csv.append(c.getLong(0)).append(',').append(c.getLong(1)).append(',')
                   .append(c.getInt(2)).append(',').append(c.getInt(3)).append(',')
                   .append(c.getInt(4)).append(',').append(c.getInt(5)).append(',');
                String name = c.getString(6);
                if (name != null) csv.append('"').append(name.replace("\"","\"\"")).append('"');
                csv.append('\n');
            }
        }
        return csv.toString();
    }
}
