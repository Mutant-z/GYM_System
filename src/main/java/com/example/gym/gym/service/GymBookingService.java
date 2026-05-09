package com.example.gym.gym.service;

import com.example.gym.auth.support.AuthConstants;
import com.example.gym.auth.support.AuthUser;
import com.example.gym.auth.support.UserContext;
import com.example.gym.common.api.ResultCode;
import com.example.gym.common.exception.BusinessException;
import com.example.gym.common.util.IdGenerator;
import com.example.gym.gym.dto.AdminBookingQueryDTO;
import com.example.gym.gym.dto.CreateGymBookingDTO;
import com.example.gym.gym.dto.MyBookingQueryDTO;
import com.example.gym.gym.entity.GymBooking;
import com.example.gym.gym.entity.GymRoom;
import com.example.gym.gym.mapper.GymBookingMapper;
import com.example.gym.gym.vo.GymBookingVO;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Duration;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.List;

@Service
public class GymBookingService {

    private static final String BOOKING_STATUS_CONFIRMED = "CONFIRMED";
    private static final String BOOKING_STATUS_CANCELED = "CANCELED";
    private static final String GYM_ROOM_STATUS_OPEN = "OPEN";

    private final GymBookingMapper gymBookingMapper;
    private final GymRoomService gymRoomService;

    public GymBookingService(GymBookingMapper gymBookingMapper, GymRoomService gymRoomService) {
        this.gymBookingMapper = gymBookingMapper;
        this.gymRoomService = gymRoomService;
    }

    @Transactional
    public GymBookingVO createBooking(CreateGymBookingDTO dto) {
        AuthUser currentUser = requireActiveMemberUser();
        validateTimeRange(dto.getStartTime(), dto.getEndTime());

        GymRoom gymRoom = gymRoomService.findExistingRoom(dto.getGymRoomId());
        validateRoomStatus(gymRoom);
        validateWithinOpenHours(gymRoom, dto.getStartTime(), dto.getEndTime());
        validateMemberBookingConflict(currentUser.getUserId(), dto.getStartTime(), dto.getEndTime());
        validateCapacity(gymRoom, dto.getHeadCount(), dto.getStartTime(), dto.getEndTime());

        GymBooking booking = new GymBooking();
        booking.setBookingNo(IdGenerator.businessId("bk"));
        booking.setMemberId(currentUser.getUserId());
        booking.setGymRoomId(gymRoom.getId());
        booking.setBookingDate(dto.getStartTime().toLocalDate());
        booking.setStartTime(dto.getStartTime());
        booking.setEndTime(dto.getEndTime());
        booking.setDurationMinutes((int) Duration.between(dto.getStartTime(), dto.getEndTime()).toMinutes());
        booking.setHeadCount(dto.getHeadCount());
        booking.setStatus(BOOKING_STATUS_CONFIRMED);
        booking.setRemark(dto.getRemark());
        gymBookingMapper.insert(booking);

        GymBookingVO vo = new GymBookingVO();
        vo.setId(booking.getId());
        vo.setBookingNo(booking.getBookingNo());
        vo.setGymRoomId(booking.getGymRoomId());
        vo.setGymRoomName(gymRoom.getName());
        vo.setBookingDate(booking.getBookingDate());
        vo.setStartTime(booking.getStartTime());
        vo.setEndTime(booking.getEndTime());
        vo.setDurationMinutes(booking.getDurationMinutes());
        vo.setHeadCount(booking.getHeadCount());
        vo.setStatus(booking.getStatus());
        vo.setRemark(booking.getRemark());
        vo.setCreatedAt(LocalDateTime.now());
        return vo;
    }

    public List<GymBookingVO> listMyBookings(MyBookingQueryDTO queryDTO) {
        AuthUser currentUser = requireActiveMemberUser();
        String status = queryDTO == null ? null : queryDTO.getStatus();
        return gymBookingMapper.findMyBookings(currentUser.getUserId(), status);
    }

    public List<GymBookingVO> listAllBookings(AdminBookingQueryDTO queryDTO) {
        requireAdminUser();
        return gymBookingMapper.findAllBookings(
                queryDTO == null ? null : queryDTO.getBookingNo(),
                queryDTO == null ? null : queryDTO.getMemberUsername(),
                queryDTO == null ? null : queryDTO.getGymRoomId(),
                queryDTO == null ? null : queryDTO.getStatus()
        );
    }

    @Transactional
    public void cancelBooking(Long bookingId) {
        AuthUser currentUser = requireActiveMemberUser();
        GymBooking booking = gymBookingMapper.findById(bookingId);
        if (booking == null) {
            throw new BusinessException("booking record does not exist");
        }
        if (!booking.getMemberId().equals(currentUser.getUserId())) {
            throw new BusinessException(ResultCode.FORBIDDEN, "you can only cancel your own booking");
        }
        if (!BOOKING_STATUS_CONFIRMED.equalsIgnoreCase(booking.getStatus())) {
            throw new BusinessException("current booking cannot be canceled");
        }
        if (!booking.getStartTime().isAfter(LocalDateTime.now())) {
            throw new BusinessException("booking that has started cannot be canceled");
        }
        gymBookingMapper.cancelById(bookingId);
    }

    @Transactional
    public void adminCancelBooking(Long bookingId) {
        requireAdminUser();
        GymBooking booking = gymBookingMapper.findById(bookingId);
        if (booking == null) {
            throw new BusinessException("booking record does not exist");
        }
        if (!BOOKING_STATUS_CONFIRMED.equalsIgnoreCase(booking.getStatus())) {
            throw new BusinessException("current booking cannot be canceled");
        }
        if (!booking.getStartTime().isAfter(LocalDateTime.now())) {
            throw new BusinessException("booking that has started cannot be canceled");
        }
        gymBookingMapper.cancelById(bookingId);
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

    private AuthUser requireAdminUser() {
        AuthUser authUser = UserContext.get();
        if (authUser == null) {
            throw new BusinessException(ResultCode.UNAUTHORIZED, "login required");
        }
        if (!AuthConstants.USER_TYPE_ADMIN.equals(authUser.getUserType())) {
            throw new BusinessException(ResultCode.FORBIDDEN, "admin login required");
        }
        return authUser;
    }

    private void validateTimeRange(LocalDateTime startTime, LocalDateTime endTime) {
        if (!startTime.isBefore(endTime)) {
            throw new BusinessException("start time must be earlier than end time");
        }
        if (!startTime.isAfter(LocalDateTime.now())) {
            throw new BusinessException("booking start time must be later than current time");
        }
    }

    private void validateRoomStatus(GymRoom gymRoom) {
        if (!GYM_ROOM_STATUS_OPEN.equalsIgnoreCase(gymRoom.getStatus())) {
            throw new BusinessException("gym room is not open for booking");
        }
    }

    private void validateWithinOpenHours(GymRoom gymRoom, LocalDateTime startTime, LocalDateTime endTime) {
        LocalTime openTime = gymRoom.getOpenTime();
        LocalTime closeTime = gymRoom.getCloseTime();
        if (openTime == null || closeTime == null) {
            return;
        }
        LocalTime bookingStart = startTime.toLocalTime();
        LocalTime bookingEnd = endTime.toLocalTime();
        if (bookingStart.isBefore(openTime) || bookingEnd.isAfter(closeTime)) {
            throw new BusinessException("booking time must be within gym room opening hours");
        }
    }

    private void validateMemberBookingConflict(Long memberId, LocalDateTime startTime, LocalDateTime endTime) {
        if (gymBookingMapper.countMemberBookingConflicts(memberId, startTime, endTime) > 0) {
            throw new BusinessException("booking time conflicts with your existing booking");
        }
    }

    private void validateCapacity(GymRoom gymRoom, Integer headCount, LocalDateTime startTime, LocalDateTime endTime) {
        Integer bookedHeadCount = gymBookingMapper.sumRoomBookedHeadCountInRange(gymRoom.getId(), startTime, endTime);
        int used = bookedHeadCount == null ? 0 : bookedHeadCount;
        if (used + headCount > gymRoom.getCapacity()) {
            throw new BusinessException("gym room capacity exceeded for the selected time slot");
        }
    }
}
