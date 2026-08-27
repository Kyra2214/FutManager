package com.futmanager.app;

import android.content.res.AssetManager;
import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import com.getcapacitor.PluginMethod;

@CapacitorPlugin(name = "NativeEngine")
public class NativeEnginePlugin extends Plugin {
    private String databasePath() throws IOException {
        File database = getContext().getDatabasePath("game.db");
        if (!database.exists()) {
            File parent = database.getParentFile();
            if (parent != null && !parent.exists() && !parent.mkdirs()) {
                throw new IOException("NATIVE_ENGINE_DATABASE_DIRECTORY_UNAVAILABLE");
            }
            AssetManager assets = getContext().getAssets();
            try (java.io.InputStream input = assets.open("public/assets/databases/game.db");
                 FileOutputStream output = new FileOutputStream(database)) {
                byte[] buffer = new byte[1024 * 1024];
                int read;
                while ((read = input.read(buffer)) != -1) output.write(buffer, 0, read);
            }
        }
        return database.getAbsolutePath();
    }

    private String execute(String action, String payload) throws Exception {
        Python python = Python.getInstance();
        String databasePath = databasePath();
        PyObject module = python.getModule("futmanager_native");
        return module.callAttr("execute", action, payload, databasePath).toJava(String.class);
    }

    private void runAction(PluginCall call, String action) {
        try {
            String result = execute(action, call.getData().toString());
            JSObject response = new JSObject(result);
            if (response.optBoolean("ok", false)) {
                call.resolve(response);
            } else {
                call.reject(response.optString("error", "NATIVE_ENGINE_FAILED"), response);
            }
        } catch (Exception error) {
            call.reject("NATIVE_ENGINE_UNAVAILABLE", error);
        }
    }

    @PluginMethod
    public void getDashboard(PluginCall call) { runAction(call, "getDashboard"); }

    @PluginMethod
    public void advanceUntilMatch(PluginCall call) { runAction(call, "advanceUntilMatch"); }

    @PluginMethod
    public void startCareer(PluginCall call) { runAction(call, "startCareer"); }

    @PluginMethod
    public void advanceWeek(PluginCall call) { runAction(call, "advanceWeek"); }

    @PluginMethod
    public void playControlledMatch(PluginCall call) { runAction(call, "playControlledMatch"); }
}
