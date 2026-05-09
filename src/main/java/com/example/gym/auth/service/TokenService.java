package com.example.gym.auth.service;

import com.example.gym.auth.support.AuthConstants;
import com.example.gym.auth.support.AuthUser;
import com.example.gym.auth.support.UserContext;
import com.example.gym.common.constants.RedisKeys;
import com.example.gym.common.util.IdGenerator;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.util.Optional;

@Service
public class TokenService {

    private final RedisTemplate<String, Object> redisTemplate;

    public TokenService(RedisTemplate<String, Object> redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    public String createToken(AuthUser authUser) {
        String token = IdGenerator.businessId("tk");
        String key = buildKey(token);
        redisTemplate.opsForValue().set(key, authUser, AuthConstants.TOKEN_TTL);
        return token;
    }

    public Optional<AuthUser> getAuthUser(String token) {
        Object value = redisTemplate.opsForValue().get(buildKey(token));
        if (value instanceof AuthUser authUser) {
            return Optional.of(authUser);
        }
        return Optional.empty();
    }

    public void refresh(String token) {
        redisTemplate.expire(buildKey(token), AuthConstants.TOKEN_TTL);
    }

    public void removeToken(String token) {
        redisTemplate.delete(buildKey(token));
    }

    public Optional<AuthUser> getCurrentUser() {
        return Optional.ofNullable(UserContext.get());
    }

    private String buildKey(String token) {
        return RedisKeys.TOKEN_PREFIX + token;
    }
}
