package com.example.gym.auth.interceptor;

import com.example.gym.auth.service.TokenService;
import com.example.gym.auth.support.AuthConstants;
import com.example.gym.auth.support.AuthUser;
import com.example.gym.auth.support.UserContext;
import com.example.gym.common.api.ApiResponse;
import com.example.gym.common.api.ResultCode;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import java.nio.charset.StandardCharsets;
import java.util.Optional;

@Component
public class AuthInterceptor implements HandlerInterceptor {

    private final TokenService tokenService;
    private final ObjectMapper objectMapper;

    public AuthInterceptor(TokenService tokenService, ObjectMapper objectMapper) {
        this.tokenService = tokenService;
        this.objectMapper = objectMapper;
    }

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        String token = resolveToken(request);
        if (token == null) {
            writeUnauthorized(response);
            return false;
        }

        Optional<AuthUser> authUserOptional = tokenService.getAuthUser(token);
        if (authUserOptional.isEmpty()) {
            writeUnauthorized(response);
            return false;
        }

        tokenService.refresh(token);
        UserContext.set(authUserOptional.get());
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) {
        UserContext.clear();
    }

    private String resolveToken(HttpServletRequest request) {
        String authorization = request.getHeader(AuthConstants.AUTHORIZATION_HEADER);
        if (authorization == null || authorization.isBlank()) {
            return null;
        }
        if (authorization.startsWith(AuthConstants.TOKEN_PREFIX)) {
            return authorization.substring(AuthConstants.TOKEN_PREFIX.length()).trim();
        }
        return authorization.trim();
    }

    private void writeUnauthorized(HttpServletResponse response) throws Exception {
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setCharacterEncoding(StandardCharsets.UTF_8.name());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.getWriter().write(objectMapper.writeValueAsString(
                ApiResponse.failure(ResultCode.UNAUTHORIZED, "login required")
        ));
    }
}
