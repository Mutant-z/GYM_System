package com.example.gym.member.service;

import com.example.gym.admin.service.AdminGuard;
import com.example.gym.common.exception.BusinessException;
import com.example.gym.member.dto.AdminMemberQueryDTO;
import com.example.gym.member.dto.AdminMemberUpdateDTO;
import com.example.gym.member.entity.Member;
import com.example.gym.member.mapper.MemberMapper;
import com.example.gym.member.vo.AdminMemberDetailVO;
import com.example.gym.member.vo.AdminMemberVO;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class AdminMemberService {

    private final AdminGuard adminGuard;
    private final MemberMapper memberMapper;

    public AdminMemberService(AdminGuard adminGuard, MemberMapper memberMapper) {
        this.adminGuard = adminGuard;
        this.memberMapper = memberMapper;
    }

    public List<AdminMemberVO> listMembers(AdminMemberQueryDTO queryDTO) {
        adminGuard.requireAdmin();
        return memberMapper.findAdminMembers(
                queryDTO == null ? null : queryDTO.getUsername(),
                queryDTO == null ? null : queryDTO.getNickname(),
                queryDTO == null ? null : queryDTO.getPhone(),
                queryDTO == null ? null : queryDTO.getMembershipStatus()
        );
    }

    public AdminMemberDetailVO getMemberDetail(Long memberId) {
        adminGuard.requireAdmin();
        AdminMemberDetailVO detailVO = memberMapper.findAdminMemberDetail(memberId);
        if (detailVO == null) {
            throw new BusinessException("member does not exist");
        }
        return detailVO;
    }

    @Transactional
    public AdminMemberDetailVO updateMember(Long memberId, AdminMemberUpdateDTO dto) {
        adminGuard.requireAdmin();
        Member member = requireExistingMember(memberId);
        validatePhoneUnique(dto.getPhone(), memberId);

        member.setNickname(dto.getNickname());
        member.setRealName(dto.getRealName());
        member.setGender(dto.getGender());
        member.setPhone(dto.getPhone());
        member.setEmail(dto.getEmail());
        member.setBirthday(dto.getBirthday());
        member.setHeightCm(dto.getHeightCm());
        member.setWeightKg(dto.getWeightKg());
        member.setFitnessGoal(dto.getFitnessGoal());
        member.setPreferredTrainingTime(dto.getPreferredTrainingTime());
        member.setInjuryNotes(dto.getInjuryNotes());
        memberMapper.updateAdminMember(member);
        return getMemberDetail(memberId);
    }

    @Transactional
    public void enableMember(Long memberId) {
        adminGuard.requireAdmin();
        requireExistingMember(memberId);
        memberMapper.updateMembershipStatus(memberId, "ACTIVE");
    }

    @Transactional
    public void disableMember(Long memberId) {
        adminGuard.requireAdmin();
        requireExistingMember(memberId);
        memberMapper.updateMembershipStatus(memberId, "DISABLED");
    }

    private Member requireExistingMember(Long memberId) {
        Member member = memberMapper.findById(memberId);
        if (member == null || Boolean.TRUE.equals(member.getDeleted())) {
            throw new BusinessException("member does not exist");
        }
        return member;
    }

    private void validatePhoneUnique(String phone, Long excludeId) {
        if (phone == null || phone.isBlank()) {
            return;
        }
        Member existing = memberMapper.findByPhone(phone);
        if (existing != null && !existing.getId().equals(excludeId) && !Boolean.TRUE.equals(existing.getDeleted())) {
            throw new BusinessException("phone already exists");
        }
    }
}
