package com.example.gym.admin.service;

import com.example.gym.auth.support.AuthConstants;
import com.example.gym.auth.support.AuthUser;
import com.example.gym.auth.support.UserContext;
import com.example.gym.common.api.ResultCode;
import com.example.gym.common.exception.BusinessException;
import org.springframework.stereotype.Component;

@Component
public class AdminGuard {

    public AuthUser requireAdmin() {
        AuthUser authUser = UserContext.get();
        if (authUser == null) {
            throw new BusinessException(ResultCode.UNAUTHORIZED, "login required");
        }
        if (!AuthConstants.USER_TYPE_ADMIN.equals(authUser.getUserType())) {
            throw new BusinessException(ResultCode.FORBIDDEN, "admin login required");
        }
        return authUser;
    }
}
