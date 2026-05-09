package com.example.gym.member.controller;

import com.example.gym.common.api.ApiResponse;
import com.example.gym.member.dto.MemberProfileUpdateDTO;
import com.example.gym.member.service.MemberProfileService;
import com.example.gym.member.vo.MemberProfileVO;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/members/me/profile")
public class MemberProfileController {

    private final MemberProfileService memberProfileService;

    public MemberProfileController(MemberProfileService memberProfileService) {
        this.memberProfileService = memberProfileService;
    }

    @GetMapping
    public ApiResponse<MemberProfileVO> getMyProfile() {
        return ApiResponse.success(memberProfileService.getMyProfile());
    }

    @PutMapping
    public ApiResponse<MemberProfileVO> updateMyProfile(@Valid @RequestBody MemberProfileUpdateDTO dto) {
        return ApiResponse.success(memberProfileService.updateMyProfile(dto));
    }
}
