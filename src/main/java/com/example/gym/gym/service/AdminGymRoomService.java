package com.example.gym.gym.service;

import com.example.gym.admin.service.AdminGuard;
import com.example.gym.common.exception.BusinessException;
import com.example.gym.gym.dto.AdminGymRoomSaveDTO;
import com.example.gym.gym.entity.GymRoom;
import com.example.gym.gym.mapper.GymRoomMapper;
import com.example.gym.gym.vo.GymRoomDetailVO;
import com.example.gym.gym.vo.GymRoomVO;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.List;

@Service
public class AdminGymRoomService {

    private final AdminGuard adminGuard;
    private final GymRoomMapper gymRoomMapper;

    public AdminGymRoomService(AdminGuard adminGuard, GymRoomMapper gymRoomMapper) {
        this.adminGuard = adminGuard;
        this.gymRoomMapper = gymRoomMapper;
    }

    public List<GymRoomVO> listRooms() {
        adminGuard.requireAdmin();
        return gymRoomMapper.findAll().stream().map(this::toRoomVO).toList();
    }

    public GymRoomDetailVO getRoomDetail(Long roomId) {
        adminGuard.requireAdmin();
        GymRoom room = requireExistingRoom(roomId);
        return toRoomDetailVO(room);
    }

    @Transactional
    public GymRoomDetailVO createRoom(AdminGymRoomSaveDTO dto) {
        adminGuard.requireAdmin();
        validateRoom(dto, null);

        GymRoom room = new GymRoom();
        fillRoom(room, dto);
        gymRoomMapper.insert(room);
        return getRoomDetail(room.getId());
    }

    @Transactional
    public GymRoomDetailVO updateRoom(Long roomId, AdminGymRoomSaveDTO dto) {
        adminGuard.requireAdmin();
        GymRoom room = requireExistingRoom(roomId);
        validateRoom(dto, roomId);
        fillRoom(room, dto);
        gymRoomMapper.update(room);
        return getRoomDetail(roomId);
    }

    @Transactional
    public void enableRoom(Long roomId) {
        adminGuard.requireAdmin();
        requireExistingRoom(roomId);
        gymRoomMapper.updateStatus(roomId, "OPEN");
    }

    @Transactional
    public void disableRoom(Long roomId) {
        adminGuard.requireAdmin();
        requireExistingRoom(roomId);
        gymRoomMapper.updateStatus(roomId, "CLOSED");
    }

    private GymRoom requireExistingRoom(Long roomId) {
        GymRoom room = gymRoomMapper.findById(roomId);
        if (room == null) {
            throw new BusinessException("gym room does not exist");
        }
        return room;
    }

    private void validateRoom(AdminGymRoomSaveDTO dto, Long excludeId) {
        if (dto.getOpenTime() != null && dto.getCloseTime() != null && !dto.getOpenTime().isBefore(dto.getCloseTime())) {
            throw new BusinessException("gym room open time must be earlier than close time");
        }
        GymRoom existing = gymRoomMapper.findByName(dto.getName());
        if (existing != null && (excludeId == null || !existing.getId().equals(excludeId))) {
            throw new BusinessException("gym room name already exists");
        }
    }

    private void fillRoom(GymRoom room, AdminGymRoomSaveDTO dto) {
        room.setName(dto.getName());
        room.setLocation(dto.getLocation());
        room.setCapacity(dto.getCapacity());
        room.setOpenTime(dto.getOpenTime());
        room.setCloseTime(dto.getCloseTime());
        room.setStatus(dto.getStatus());
        room.setDescription(dto.getDescription());
    }

    private GymRoomVO toRoomVO(GymRoom room) {
        GymRoomVO vo = new GymRoomVO();
        vo.setId(room.getId());
        vo.setName(room.getName());
        vo.setLocation(room.getLocation());
        vo.setCapacity(room.getCapacity());
        vo.setOpenTime(room.getOpenTime());
        vo.setCloseTime(room.getCloseTime());
        vo.setStatus(room.getStatus());
        vo.setDescription(room.getDescription());
        return vo;
    }

    private GymRoomDetailVO toRoomDetailVO(GymRoom room) {
        GymRoomDetailVO vo = new GymRoomDetailVO();
        vo.setId(room.getId());
        vo.setName(room.getName());
        vo.setLocation(room.getLocation());
        vo.setCapacity(room.getCapacity());
        vo.setOpenTime(room.getOpenTime());
        vo.setCloseTime(room.getCloseTime());
        vo.setStatus(room.getStatus());
        vo.setDescription(room.getDescription());
        vo.setTodayBookedHeadCount(gymRoomMapper.sumTodayBookedHeadCount(room.getId(), LocalDate.now()));
        vo.setBookable("OPEN".equalsIgnoreCase(room.getStatus()));
        return vo;
    }
}
