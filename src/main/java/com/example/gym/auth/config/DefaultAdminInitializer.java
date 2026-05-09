package com.example.gym.auth.config;

import com.example.gym.auth.support.AuthConstants;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

@Component
public class DefaultAdminInitializer implements ApplicationRunner {

    private static final Logger log = LoggerFactory.getLogger(DefaultAdminInitializer.class);

    private final JdbcTemplate jdbcTemplate;
    private final PasswordEncoder passwordEncoder;
    private final boolean enabled;
    private final String username;
    private final String password;

    public DefaultAdminInitializer(
            JdbcTemplate jdbcTemplate,
            PasswordEncoder passwordEncoder,
            @Value("${gym.default-admin.enabled:true}") boolean enabled,
            @Value("${gym.default-admin.username:admin001}") String username,
            @Value("${gym.default-admin.password:123456}") String password
    ) {
        this.jdbcTemplate = jdbcTemplate;
        this.passwordEncoder = passwordEncoder;
        this.enabled = enabled;
        this.username = username;
        this.password = password;
    }

    @Override
    public void run(ApplicationArguments args) {
        if (!enabled) {
            log.info("Default admin initialization is disabled.");
            return;
        }

        Integer count = jdbcTemplate.queryForObject(
                "SELECT COUNT(1) FROM admin WHERE username = ?",
                Integer.class,
                username
        );
        if (count == null || count == 0) {
            jdbcTemplate.update(
                    """
                            INSERT INTO admin (username, password_hash, name, phone, role, status)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                    username,
                    passwordEncoder.encode(password),
                    "系统管理员",
                    null,
                    "SUPER_ADMIN",
                    AuthConstants.STATUS_ACTIVE
            );
            log.info("Default admin account created: username={}", username);
            return;
        }

        jdbcTemplate.update(
                """
                        UPDATE admin
                        SET password_hash = ?, status = ?, role = COALESCE(NULLIF(role, ''), ?)
                        WHERE username = ?
                        """,
                passwordEncoder.encode(password),
                AuthConstants.STATUS_ACTIVE,
                "SUPER_ADMIN",
                username
        );
        log.info("Default admin account ensured active: username={}", username);
    }
}
