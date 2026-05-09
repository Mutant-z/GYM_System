package com.example.gym.member.controller;

import com.example.gym.common.api.ApiResponse;
import com.example.gym.member.dto.AdminMemberQueryDTO;
import com.example.gym.member.dto.AdminMemberUpdateDTO;
import com.example.gym.member.service.AdminMemberService;
import com.example.gym.member.vo.AdminMemberDetailVO;
import com.example.gym.member.vo.AdminMemberVO;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/admin/members")
public class AdminMemberController {

    private final AdminMemberService adminMemberService;

    public AdminMemberController(AdminMemberService adminMemberService) {
        this.adminMemberService = adminMemberService;
    }

    @GetMapping
    public ApiResponse<List<AdminMemberVO>> listMembers(
            @RequestParam(value = "username", required = false) String username,
            @RequestParam(value = "nickname", required = false) String nickname,
            @RequestParam(value = "phone", required = false) String phone,
            @RequestParam(value = "membershipStatus", required = false) String membershipStatus
    ) {
        AdminMemberQueryDTO queryDTO = new AdminMemberQueryDTO();
        queryDTO.setUsername(username);
        queryDTO.setNickname(nickname);
        queryDTO.setPhone(phone);
        queryDTO.setMembershipStatus(membershipStatus);
        return ApiResponse.success(adminMemberService.listMembers(queryDTO));
    }

    @GetMapping("/{id}")
    public ApiResponse<AdminMemberDetailVO> getMemberDetail(@PathVariable("id") Long id) {
        return ApiResponse.success(adminMemberService.getMemberDetail(id));
    }

    @PutMapping("/{id}")
    public ApiResponse<AdminMemberDetailVO> updateMember(@PathVariable("id") Long id, @Valid @RequestBody AdminMemberUpdateDTO dto) {
        return ApiResponse.success(adminMemberService.updateMember(id, dto));
    }

    @PostMapping("/{id}/enable")
    public ApiResponse<Void> enableMember(@PathVariable("id") Long id) {
        adminMemberService.enableMember(id);
        return ApiResponse.success();
    }

    @PostMapping("/{id}/disable")
    public ApiResponse<Void> disableMember(@PathVariable("id") Long id) {
        adminMemberService.disableMember(id);
        return ApiResponse.success();
    }
}
