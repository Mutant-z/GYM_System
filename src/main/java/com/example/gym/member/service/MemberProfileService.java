package com.example.gym.member.service;

import com.example.gym.auth.support.AuthConstants;
import com.example.gym.auth.support.AuthUser;
import com.example.gym.auth.support.UserContext;
import com.example.gym.common.api.ResultCode;
import com.example.gym.common.exception.BusinessException;
import com.example.gym.member.dto.MemberProfileUpdateDTO;
import com.example.gym.member.entity.Member;
import com.example.gym.member.mapper.MemberMapper;
import com.example.gym.member.vo.MemberProfileVO;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class MemberProfileService {

    private final MemberMapper memberMapper;

    public MemberProfileService(MemberMapper memberMapper) {
        this.memberMapper = memberMapper;
    }

    public MemberProfileVO getMyProfile() {
        AuthUser currentUser = requireActiveMemberUser();
        return toVO(requireExistingMember(currentUser.getUserId()));
    }

    @Transactional
    public MemberProfileVO updateMyProfile(MemberProfileUpdateDTO dto) {
        AuthUser currentUser = requireActiveMemberUser();
        Member member = requireExistingMember(currentUser.getUserId());
        validatePhoneUnique(dto.getPhone(), member.getId());

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

        memberMapper.updateMemberProfile(member);
        return toVO(requireExistingMember(member.getId()));
    }

    private AuthUser requireMemberUser() {
        AuthUser authUser = UserContext.get();
        if (authUser == null) {
            throw new BusinessException(ResultCode.UNAUTHORIZED, "login required");
        }
        if (!AuthConstants.USER_TYPE_MEMBER.equals(authUser.getUserType())) {
            throw new BusinessException(ResultCode.FORBIDDEN, "member login required");
        }
        return authUser;
    }

    private AuthUser requireActiveMemberUser() {
        AuthUser authUser = requireMemberUser();
        if (!AuthConstants.isMemberActiveStatus(authUser.getStatus())) {
            throw new BusinessException(ResultCode.FORBIDDEN, "member account is not enabled");
        }
        return authUser;
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

    private MemberProfileVO toVO(Member member) {
        MemberProfileVO vo = new MemberProfileVO();
        vo.setId(member.getId());
        vo.setUsername(member.getUsername());
        vo.setNickname(member.getNickname());
        vo.setRealName(member.getRealName());
        vo.setGender(member.getGender());
        vo.setPhone(member.getPhone());
        vo.setEmail(member.getEmail());
        vo.setBirthday(member.getBirthday());
        vo.setHeightCm(member.getHeightCm());
        vo.setWeightKg(member.getWeightKg());
        vo.setFitnessGoal(member.getFitnessGoal());
        vo.setPreferredTrainingTime(member.getPreferredTrainingTime());
        vo.setInjuryNotes(member.getInjuryNotes());
        vo.setMembershipStatus(member.getMembershipStatus());
        vo.setLastLoginAt(member.getLastLoginAt());
        vo.setCreatedAt(member.getCreatedAt());
        vo.setUpdatedAt(member.getUpdatedAt());
        return vo;
    }
}
