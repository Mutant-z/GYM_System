package com.example.gym.auth.support;

import java.time.Duration;

public final class AuthConstants {

    public static final String AUTHORIZATION_HEADER = "Authorization";
    public static final String TOKEN_PREFIX = "Bearer ";
    public static final Duration TOKEN_TTL = Duration.ofHours(2);
    public static final String USER_TYPE_MEMBER = "MEMBER";
    public static final String USER_TYPE_ADMIN = "ADMIN";
    public static final String STATUS_ACTIVE = "ACTIVE";
    public static final String STATUS_PENDING = "PENDING";
    public static final String STATUS_DISABLED = "DISABLED";

    private AuthConstants() {
    }

    public static boolean isMemberLoginAllowedStatus(String status) {
        return status != null && !STATUS_DISABLED.equalsIgnoreCase(status);
    }

    public static boolean isMemberActiveStatus(String status) {
        return STATUS_ACTIVE.equalsIgnoreCase(status);
    }
}
