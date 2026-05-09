package com.example.gym.common.filter;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
public class OrderRequestTraceFilter extends OncePerRequestFilter {

    private static final DateTimeFormatter FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss.SSS");
    private static final String ORDER_PATH_PREFIX = "/api/orders";

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        String uri = request.getRequestURI();
        return uri == null || !uri.startsWith(ORDER_PATH_PREFIX);
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {
        long start = System.currentTimeMillis();
        String method = request.getMethod();
        String uri = request.getRequestURI();
        String query = request.getQueryString();
        String fullPath = query == null || query.isBlank() ? uri : uri + "?" + query;
        boolean hasAuthorization = request.getHeader("Authorization") != null
                && !request.getHeader("Authorization").isBlank();

        String startAt = LocalDateTime.now().format(FORMATTER);
        System.out.println(
                startAt
                        + " [orders] START "
                        + method
                        + " "
                        + fullPath
                        + " auth="
                        + (hasAuthorization ? "yes" : "no")
        );
        try {
            filterChain.doFilter(request, response);
        } finally {
            long durationMs = System.currentTimeMillis() - start;
            String endAt = LocalDateTime.now().format(FORMATTER);
            System.out.println(
                    endAt
                            + " [orders] END   "
                            + method
                            + " "
                            + fullPath
                            + " -> "
                            + response.getStatus()
                            + " ("
                            + durationMs
                            + " ms, auth="
                            + (hasAuthorization ? "yes" : "no")
                            + ")"
            );
        }
    }
}
