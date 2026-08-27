package com.futmanager.app;

import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(android.os.Bundle savedInstanceState) {
        registerPlugin(NativeEnginePlugin.class);
        super.onCreate(savedInstanceState);
    }
}
