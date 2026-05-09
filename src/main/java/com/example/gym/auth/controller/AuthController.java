package com.example.gym.auth.controller;

import com.example.gym.auth.dto.AdminLoginDTO;
import com.example.gym.auth.dto.MemberLoginDTO;
import com.example.gym.auth.dto.MemberRegisterDTO;
import com.example.gym.auth.service.AuthService;
import com.example.gym.auth.vo.CurrentUserVO;
import com.example.gym.auth.vo.LoginVO;
import com.example.gym.auth.vo.MemberRegisterVO;
import com.example.gym.common.api.ApiResponse;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/auth")
public class AuthController {

    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/member/login")
    public ApiResponse<LoginVO> memberLogin(@Valid @RequestBody MemberLoginDTO dto) {
        return ApiResponse.success(authService.memberLogin(dto));
    }

    @PostMapping("/member/register")
    public ApiResponse<MemberRegisterVO> memberRegister(@Valid @RequestBody MemberRegisterDTO dto) {
        return ApiResponse.success(authService.memberRegister(dto));
    }

    @PostMapping("/admin/login")
    public ApiResponse<LoginVO> adminLogin(@Valid @RequestBody AdminLoginDTO dto) {
        return ApiResponse.success(authService.adminLogin(dto));
    }

    @GetMapping("/me")
    public ApiResponse<CurrentUserVO> currentUser() {
        return ApiResponse.success(authService.currentUser());
    }

    @PostMapping("/logout")
    public ApiResponse<Void> logout(@RequestHeader(value = "Authorization", required = false) String authorization) {
        authService.logout(extractToken(authorization));
        return ApiResponse.success();
    }

    private String extractToken(String authorization) {
        if (authorization == null || authorization.isBlank()) {
            return null;
        }
        if (authorization.startsWith("Bearer ")) {
            return authorization.substring("Bearer ".length()).trim();
        }
        return authorization.trim();
    }
}
