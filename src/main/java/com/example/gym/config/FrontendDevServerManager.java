package com.example.gym.config;

import jakarta.annotation.PreDestroy;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.ApplicationListener;
import org.springframework.stereotype.Component;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

@Component
public class FrontendDevServerManager implements ApplicationListener<ApplicationReadyEvent> {

    private static final Logger log = LoggerFactory.getLogger(FrontendDevServerManager.class);

    private final FrontendDevServerProperties properties;
    private final AtomicBoolean started = new AtomicBoolean(false);
    private volatile Process frontendProcess;

    public FrontendDevServerManager(FrontendDevServerProperties properties) {
        this.properties = properties;
    }

    @Override
    public void onApplicationEvent(ApplicationReadyEvent event) {
        startFrontend();
    }

    public synchronized void startFrontend() {
        if (!properties.isEnabled()) {
            log.info("Frontend auto-start is disabled.");
            return;
        }
        if (frontendProcess != null && frontendProcess.isAlive()) {
            log.info("Frontend process is already running.");
            return;
        }

        Path workingDirectory = Path.of(properties.getWorkingDirectory());
        if (!Files.isDirectory(workingDirectory)) {
            log.warn("Frontend working directory does not exist: {}", workingDirectory);
            return;
        }

        List<String> command = properties.getCommand();
        if (command == null || command.isEmpty()) {
            log.warn("Frontend command is empty; skip starting frontend process.");
            return;
        }

        ProcessBuilder processBuilder = new ProcessBuilder(command);
        processBuilder.directory(workingDirectory.toFile());
        processBuilder.redirectErrorStream(true);

        try {
            frontendProcess = processBuilder.start();
            started.set(true);
            log.info("Frontend process started: {} (cwd={})", String.join(" ", command), workingDirectory);
            pumpOutput(frontendProcess);
        } catch (IOException ex) {
            started.set(false);
            log.error("Failed to start frontend process.", ex);
        }
    }

    private void pumpOutput(Process process) {
        Thread logThread = new Thread(() -> {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    log.info("[frontend] {}", line);
                }
            } catch (IOException ex) {
                if (started.get()) {
                    log.warn("Frontend output stream stopped unexpectedly.", ex);
                }
            }
        }, "frontend-dev-server-output");
        logThread.setDaemon(true);
        logThread.start();
    }

    @PreDestroy
    public synchronized void stopFrontend() {
        started.set(false);
        Process process = frontendProcess;
        frontendProcess = null;
        if (process == null) {
            return;
        }

        process.destroy();
        try {
            if (!process.waitFor(properties.getStopTimeoutSeconds(), TimeUnit.SECONDS)) {
                process.destroyForcibly();
                process.waitFor(properties.getStopTimeoutSeconds(), TimeUnit.SECONDS);
            }
            log.info("Frontend process stopped.");
        } catch (InterruptedException ex) {
            Thread.currentThread().interrupt();
            process.destroyForcibly();
            log.warn("Interrupted while stopping frontend process.", ex);
        }
    }
}
