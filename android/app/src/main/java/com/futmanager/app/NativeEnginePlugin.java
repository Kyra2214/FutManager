package com.futmanager.app;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.PluginMethod;
import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.security.MessageDigest;
import java.util.Locale;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import org.json.JSONObject;

@CapacitorPlugin(name = "NativeEngine")
public class NativeEnginePlugin extends Plugin {
    private static final String DATA_DIRECTORY = "futmanager-data";
    private static final String DATA_MANIFEST = "data-manifest.json";
    private static final String DATABASE_ENTRY = "database/game.db";

    private File dataDirectory() {
        return new File(getContext().getFilesDir(), DATA_DIRECTORY);
    }

    private File preparedDatabase() {
        return new File(dataDirectory(), DATABASE_ENTRY);
    }

    private File databasePath() throws IOException {
        File database = getContext().getDatabasePath("game.db");
        if (!database.exists()) {
            throw new IOException("NATIVE_ENGINE_DATA_NOT_PREPARED");
        }
        return database;
    }

    private void copyFile(File source, File destination) throws IOException {
        File parent = destination.getParentFile();
        if (parent != null && !parent.exists() && !parent.mkdirs()) {
            throw new IOException("NATIVE_ENGINE_DATABASE_DIRECTORY_UNAVAILABLE");
        }
        try (InputStream input = new BufferedInputStream(new FileInputStream(source));
             OutputStream output = new BufferedOutputStream(new FileOutputStream(destination))) {
            byte[] buffer = new byte[1024 * 1024];
            int read;
            while ((read = input.read(buffer)) != -1) output.write(buffer, 0, read);
        }
    }

    private String sha256(File file) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try (InputStream input = new BufferedInputStream(new FileInputStream(file))) {
            byte[] buffer = new byte[1024 * 1024];
            int read;
            while ((read = input.read(buffer)) != -1) digest.update(buffer, 0, read);
        }
        StringBuilder result = new StringBuilder();
        for (byte value : digest.digest()) result.append(String.format(Locale.ROOT, "%02x", value));
        return result.toString();
    }

    private void deleteTree(File root) throws IOException {
        if (!root.exists()) return;
        File[] children = root.listFiles();
        if (children != null) for (File child : children) deleteTree(child);
        if (!root.delete()) throw new IOException("NATIVE_ENGINE_DATA_CLEANUP_FAILED");
    }

    private void extractZip(File zipFile, File destination) throws IOException {
        String destinationPath = destination.getCanonicalPath() + File.separator;
        try (ZipInputStream input = new ZipInputStream(new BufferedInputStream(new FileInputStream(zipFile)))) {
            ZipEntry entry;
            byte[] buffer = new byte[1024 * 1024];
            while ((entry = input.getNextEntry()) != null) {
                File target = new File(destination, entry.getName());
                String targetPath = target.getCanonicalPath();
                if (!targetPath.startsWith(destinationPath)) throw new IOException("NATIVE_ENGINE_INVALID_PACKAGE_PATH");
                if (entry.isDirectory()) {
                    if (!target.mkdirs() && !target.isDirectory()) throw new IOException("NATIVE_ENGINE_PACKAGE_EXTRACTION_FAILED");
                } else {
                    File parent = target.getParentFile();
                    if (parent != null && !parent.exists() && !parent.mkdirs()) throw new IOException("NATIVE_ENGINE_PACKAGE_EXTRACTION_FAILED");
                    try (OutputStream output = new BufferedOutputStream(new FileOutputStream(target))) {
                        int read;
                        while ((read = input.read(buffer)) != -1) output.write(buffer, 0, read);
                    }
                }
                input.closeEntry();
            }
        }
    }

    private File download(String sourceUrl, File destination) throws IOException {
        HttpURLConnection connection = (HttpURLConnection) new URL(sourceUrl).openConnection();
        connection.setConnectTimeout(20_000);
        connection.setReadTimeout(120_000);
        connection.setInstanceFollowRedirects(true);
        connection.setRequestMethod("GET");
        int response = connection.getResponseCode();
        if (response < 200 || response >= 300) throw new IOException("NATIVE_ENGINE_DOWNLOAD_HTTP_" + response);
        try (InputStream input = new BufferedInputStream(connection.getInputStream());
             OutputStream output = new BufferedOutputStream(new FileOutputStream(destination))) {
            byte[] buffer = new byte[1024 * 1024];
            int read;
            while ((read = input.read(buffer)) != -1) output.write(buffer, 0, read);
        } finally {
            connection.disconnect();
        }
        return destination;
    }

    private File safeDataFile(String relativePath) throws IOException {
        File root = dataDirectory().getCanonicalFile();
        File target = new File(root, relativePath).getCanonicalFile();
        String rootPath = root.getPath() + File.separator;
        if (!target.getPath().startsWith(rootPath)) throw new IOException("NATIVE_ENGINE_INVALID_DATA_PATH");
        return target;
    }

    @PluginMethod
    public void readDataFile(PluginCall call) {
        try {
            File file = safeDataFile(call.getString("path", ""));
            JSObject result = new JSObject();
            result.put("content", new String(Files.readAllBytes(file.toPath()), StandardCharsets.UTF_8));
            call.resolve(result);
        } catch (Exception error) {
            call.reject("NATIVE_ENGINE_DATA_FILE_UNAVAILABLE", error);
        }
    }

    @PluginMethod
    public void getDataAssetUrl(PluginCall call) {
        try {
            File file = safeDataFile(call.getString("path", ""));
            if (!file.isFile()) throw new IOException("NATIVE_ENGINE_DATA_ASSET_UNAVAILABLE");
            JSObject result = new JSObject();
            result.put("uri", "file://" + file.getAbsolutePath());
            call.resolve(result);
        } catch (Exception error) {
            call.reject("NATIVE_ENGINE_DATA_ASSET_UNAVAILABLE", error);
        }
    }

    @PluginMethod
    public void getDataStatus(PluginCall call) {
        JSObject result = new JSObject();
        File manifest = new File(dataDirectory(), DATA_MANIFEST);
        boolean ready = preparedDatabase().isFile() && manifest.isFile();
        result.put("ready", ready);
        result.put("version", ready ? readVersion(manifest) : JSONObject.NULL);
        call.resolve(result);
    }

    private String readVersion(File manifest) {
        try {
            return new JSONObject(new String(Files.readAllBytes(manifest.toPath()), StandardCharsets.UTF_8)).optString("version", "unknown");
        } catch (Exception ignored) {
            return "unknown";
        }
    }

    @PluginMethod
    public void prepareData(PluginCall call) {
        String manifestUrl = call.getString("manifestUrl", "");
        if (manifestUrl.isEmpty()) {
            call.reject("NATIVE_ENGINE_DATA_MANIFEST_URL_REQUIRED");
            return;
        }
        new Thread(() -> {
            File work = null;
            try {
                work = new File(getContext().getCacheDir(), "futmanager-data-download-" + System.currentTimeMillis());
                if (!work.mkdirs()) throw new IOException("NATIVE_ENGINE_DATA_WORK_DIRECTORY_UNAVAILABLE");
                File manifestFile = download(manifestUrl, new File(work, "manifest.json"));
                JSONObject manifest = new JSONObject(new String(Files.readAllBytes(manifestFile.toPath()), StandardCharsets.UTF_8));
                String packageUrl = new URL(new URL(manifestUrl), manifest.getString("packageUrl")).toString();
                String expectedHash = manifest.getString("packageSha256").toLowerCase(Locale.ROOT);
                File packageFile = download(packageUrl, new File(work, "package.zip"));
                long packageBytes = packageFile.length();
                String actualHash = sha256(packageFile);
                if (!actualHash.equals(expectedHash)) throw new IOException("NATIVE_ENGINE_DATA_CHECKSUM_MISMATCH");
                File extracted = new File(work, "extracted");
                if (!extracted.mkdirs()) throw new IOException("NATIVE_ENGINE_DATA_EXTRACTION_DIRECTORY_UNAVAILABLE");
                extractZip(packageFile, extracted);
                File sourceDatabase = new File(extracted, DATABASE_ENTRY);
                if (!sourceDatabase.isFile()) throw new IOException("NATIVE_ENGINE_DATA_DATABASE_MISSING");
                File stagedData = new File(work, "staged-data");
                if (!stagedData.mkdirs()) throw new IOException("NATIVE_ENGINE_DATA_STAGING_UNAVAILABLE");
                copyTree(extracted, stagedData);
                File installedDatabase = getContext().getDatabasePath("game.db");
                File oldData = dataDirectory();
                File backupData = new File(getContext().getCacheDir(), "futmanager-data-previous-" + System.currentTimeMillis());
                if (oldData.exists() && !oldData.renameTo(backupData)) throw new IOException("NATIVE_ENGINE_DATA_INSTALL_FAILED");
                if (!stagedData.renameTo(oldData)) throw new IOException("NATIVE_ENGINE_DATA_INSTALL_FAILED");
                copyFile(preparedDatabase(), installedDatabase);
                Files.write(new File(oldData, DATA_MANIFEST).toPath(), manifest.toString(2).getBytes(StandardCharsets.UTF_8));
                deleteTree(backupData);
                deleteTree(work);
                JSObject result = new JSObject();
                result.put("ready", true);
                result.put("version", manifest.optString("version", "unknown"));
                result.put("bytes", packageBytes);
                call.resolve(result);
            } catch (Exception error) {
                if (work != null) {
                    try { deleteTree(work); } catch (Exception ignored) { }
                }
                call.reject(error.getMessage() == null ? "NATIVE_ENGINE_DATA_PREPARATION_FAILED" : error.getMessage(), error);
            }
        }).start();
    }

    private void copyTree(File source, File destination) throws IOException {
        if (source.isDirectory()) {
            if (!destination.exists() && !destination.mkdirs()) throw new IOException("NATIVE_ENGINE_DATA_COPY_FAILED");
            File[] children = source.listFiles();
            if (children != null) for (File child : children) copyTree(child, new File(destination, child.getName()));
        } else {
            copyFile(source, destination);
        }
    }

    private String execute(String action, String payload) throws Exception {
        Python python = Python.getInstance();
        String database = databasePath().getAbsolutePath();
        PyObject module = python.getModule("futmanager_native");
        return module.callAttr("execute", action, payload, database).toJava(String.class);
    }

    private void runAction(PluginCall call, String action) {
        try {
            String result = execute(action, call.getData().toString());
            JSObject response = new JSObject(result);
            if (response.optBoolean("ok", false)) call.resolve(response);
            else call.reject(response.optString("error", "NATIVE_ENGINE_FAILED"), response);
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
