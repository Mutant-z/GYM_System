package com.example.gym.auth.support;

import org.springframework.security.crypto.password.PasswordEncoder;

public final class PasswordUtils {

    private PasswordUtils() {
    }

    public static boolean matches(PasswordEncoder passwordEncoder, String rawPassword, String passwordHash) {
        if (passwordHash == null || passwordHash.isBlank()) {
            return false;
        }
        if (passwordHash.startsWith("$2a$") || passwordHash.startsWith("$2b$") || passwordHash.startsWith("$2y$")) {
            return passwordEncoder.matches(rawPassword, passwordHash);
        }
        return passwordHash.equals(rawPassword);
    }
}
