package com.example.gym.gym.service;

import com.example.gym.common.exception.BusinessException;
import com.example.gym.gym.entity.GymRoom;
import com.example.gym.gym.mapper.GymRoomMapper;
import com.example.gym.gym.vo.GymRoomDetailVO;
import com.example.gym.gym.vo.GymRoomVO;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.List;

@Service
public class GymRoomService {

    private final GymRoomMapper gymRoomMapper;

    public GymRoomService(GymRoomMapper gymRoomMapper) {
        this.gymRoomMapper = gymRoomMapper;
    }

    public List<GymRoomVO> listRooms() {
        return gymRoomMapper.findAll().stream().map(this::toRoomVO).toList();
    }

    public GymRoomDetailVO getRoomDetail(Long id) {
        GymRoom gymRoom = findExistingRoom(id);
        GymRoomDetailVO vo = toRoomDetailVO(gymRoom);
        vo.setTodayBookedHeadCount(gymRoomMapper.sumTodayBookedHeadCount(id, LocalDate.now()));
        vo.setBookable("OPEN".equalsIgnoreCase(gymRoom.getStatus()));
        return vo;
    }

    public GymRoom findExistingRoom(Long id) {
        GymRoom gymRoom = gymRoomMapper.findById(id);
        if (gymRoom == null) {
            throw new BusinessException("gym room does not exist");
        }
        return gymRoom;
    }

    private GymRoomVO toRoomVO(GymRoom gymRoom) {
        GymRoomVO vo = new GymRoomVO();
        vo.setId(gymRoom.getId());
        vo.setName(gymRoom.getName());
        vo.setLocation(gymRoom.getLocation());
        vo.setCapacity(gymRoom.getCapacity());
        vo.setOpenTime(gymRoom.getOpenTime());
        vo.setCloseTime(gymRoom.getCloseTime());
        vo.setStatus(gymRoom.getStatus());
        vo.setDescription(gymRoom.getDescription());
        return vo;
    }

    private GymRoomDetailVO toRoomDetailVO(GymRoom gymRoom) {
        GymRoomDetailVO vo = new GymRoomDetailVO();
        vo.setId(gymRoom.getId());
        vo.setName(gymRoom.getName());
        vo.setLocation(gymRoom.getLocation());
        vo.setCapacity(gymRoom.getCapacity());
        vo.setOpenTime(gymRoom.getOpenTime());
        vo.setCloseTime(gymRoom.getCloseTime());
        vo.setStatus(gymRoom.getStatus());
        vo.setDescription(gymRoom.getDescription());
        return vo;
    }
}
