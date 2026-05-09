package com.example.gym.auth.service;

import com.example.gym.admin.entity.Admin;
import com.example.gym.admin.mapper.AdminMapper;
import com.example.gym.auth.dto.AdminLoginDTO;
import com.example.gym.auth.dto.MemberLoginDTO;
import com.example.gym.auth.dto.MemberRegisterDTO;
import com.example.gym.auth.support.AuthConstants;
import com.example.gym.auth.support.AuthUser;
import com.example.gym.auth.support.PasswordUtils;
import com.example.gym.auth.vo.CurrentUserVO;
import com.example.gym.auth.vo.LoginVO;
import com.example.gym.auth.vo.MemberRegisterVO;
import com.example.gym.common.api.ResultCode;
import com.example.gym.common.exception.BusinessException;
import com.example.gym.member.entity.Member;
import com.example.gym.member.mapper.MemberMapper;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
public class AuthService {

    private final MemberMapper memberMapper;
    private final AdminMapper adminMapper;
    private final PasswordEncoder passwordEncoder;
    private final TokenService tokenService;

    public AuthService(
            MemberMapper memberMapper,
            AdminMapper adminMapper,
            PasswordEncoder passwordEncoder,
            TokenService tokenService
    ) {
        this.memberMapper = memberMapper;
        this.adminMapper = adminMapper;
        this.passwordEncoder = passwordEncoder;
        this.tokenService = tokenService;
    }

    public LoginVO memberLogin(MemberLoginDTO dto) {
        Member member = memberMapper.findByUsername(dto.getUsername());
        if (member == null) {
            throw new BusinessException(ResultCode.UNAUTHORIZED, "member account or password is invalid");
        }
        if (!AuthConstants.isMemberLoginAllowedStatus(member.getMembershipStatus())) {
            throw new BusinessException(ResultCode.FORBIDDEN, "member account is disabled");
        }
        if (!PasswordUtils.matches(passwordEncoder, dto.getPassword(), member.getPasswordHash())) {
            throw new BusinessException(ResultCode.UNAUTHORIZED, "member account or password is invalid");
        }

        LocalDateTime loginAt = LocalDateTime.now();
        memberMapper.updateLastLoginAt(member.getId(), loginAt);
        AuthUser authUser = buildMemberAuthUser(member, loginAt);
        String token = tokenService.createToken(authUser);
        return toLoginVO(authUser, token);
    }

    public LoginVO adminLogin(AdminLoginDTO dto) {
        Admin admin = adminMapper.findByUsername(dto.getUsername());
        if (admin == null) {
            throw new BusinessException(ResultCode.UNAUTHORIZED, "admin account or password is invalid");
        }
        if (!AuthConstants.STATUS_ACTIVE.equalsIgnoreCase(admin.getStatus())) {
            throw new BusinessException(ResultCode.FORBIDDEN, "admin account is inactive");
        }
        if (!PasswordUtils.matches(passwordEncoder, dto.getPassword(), admin.getPasswordHash())) {
            throw new BusinessException(ResultCode.UNAUTHORIZED, "admin account or password is invalid");
        }

        LocalDateTime loginAt = LocalDateTime.now();
        adminMapper.updateLastLoginAt(admin.getId(), loginAt);
        AuthUser authUser = buildAdminAuthUser(admin, loginAt);
        String token = tokenService.createToken(authUser);
        return toLoginVO(authUser, token);
    }

    public MemberRegisterVO memberRegister(MemberRegisterDTO dto) {
        if (memberMapper.findByUsername(dto.getUsername()) != null) {
            throw new BusinessException("username already exists");
        }
        if (memberMapper.findByPhone(dto.getPhone()) != null) {
            throw new BusinessException("phone already exists");
        }

        Member member = new Member();
        member.setUsername(dto.getUsername());
        member.setPasswordHash(passwordEncoder.encode(dto.getPassword()));
        member.setNickname(dto.getNickname());
        member.setPhone(dto.getPhone());
        member.setEmail(dto.getEmail());
        member.setMembershipStatus(AuthConstants.STATUS_PENDING);
        member.setDeleted(Boolean.FALSE);
        memberMapper.insertMember(member);

        MemberRegisterVO vo = new MemberRegisterVO();
        vo.setUserId(member.getId());
        vo.setUsername(member.getUsername());
        vo.setDisplayName(member.getNickname());
        vo.setStatus(member.getMembershipStatus());
        return vo;
    }

    public CurrentUserVO currentUser() {
        AuthUser authUser = tokenService.getCurrentUser()
                .orElseThrow(() -> new BusinessException(ResultCode.UNAUTHORIZED, "login required"));
        CurrentUserVO vo = new CurrentUserVO();
        vo.setUserId(authUser.getUserId());
        vo.setUsername(authUser.getUsername());
        vo.setDisplayName(authUser.getDisplayName());
        vo.setUserType(authUser.getUserType());
        vo.setRole(authUser.getRole());
        vo.setStatus(authUser.getStatus());
        vo.setLoginAt(authUser.getLoginAt());
        return vo;
    }

    public void logout(String token) {
        if (token != null && !token.isBlank()) {
            tokenService.removeToken(token);
        }
    }

    private AuthUser buildMemberAuthUser(Member member, LocalDateTime loginAt) {
        AuthUser authUser = new AuthUser();
        authUser.setUserId(member.getId());
        authUser.setUsername(member.getUsername());
        authUser.setDisplayName(member.getNickname());
        authUser.setUserType(AuthConstants.USER_TYPE_MEMBER);
        authUser.setRole(AuthConstants.USER_TYPE_MEMBER);
        authUser.setStatus(member.getMembershipStatus());
        authUser.setLoginAt(loginAt);
        return authUser;
    }

    private AuthUser buildAdminAuthUser(Admin admin, LocalDateTime loginAt) {
        AuthUser authUser = new AuthUser();
        authUser.setUserId(admin.getId());
        authUser.setUsername(admin.getUsername());
        authUser.setDisplayName(admin.getName());
        authUser.setUserType(AuthConstants.USER_TYPE_ADMIN);
        authUser.setRole(admin.getRole());
        authUser.setStatus(admin.getStatus());
        authUser.setLoginAt(loginAt);
        return authUser;
    }

    private LoginVO toLoginVO(AuthUser authUser, String token) {
        LoginVO vo = new LoginVO();
        vo.setToken(token);
        vo.setUserId(authUser.getUserId());
        vo.setUsername(authUser.getUsername());
        vo.setDisplayName(authUser.getDisplayName());
        vo.setUserType(authUser.getUserType());
        vo.setRole(authUser.getRole());
        vo.setStatus(authUser.getStatus());
        return vo;
    }
}
