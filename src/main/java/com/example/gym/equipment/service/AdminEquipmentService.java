package com.example.gym.equipment.service;

import com.example.gym.admin.service.AdminGuard;
import com.example.gym.common.exception.BusinessException;
import com.example.gym.equipment.dto.AdminEquipmentSaveDTO;
import com.example.gym.equipment.entity.Equipment;
import com.example.gym.equipment.mapper.EquipmentMapper;
import com.example.gym.equipment.vo.EquipmentVO;
import com.example.gym.gym.mapper.GymRoomMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class AdminEquipmentService {

    private final AdminGuard adminGuard;
    private final EquipmentMapper equipmentMapper;
    private final GymRoomMapper gymRoomMapper;

    public AdminEquipmentService(AdminGuard adminGuard, EquipmentMapper equipmentMapper, GymRoomMapper gymRoomMapper) {
        this.adminGuard = adminGuard;
        this.equipmentMapper = equipmentMapper;
        this.gymRoomMapper = gymRoomMapper;
    }

    public List<EquipmentVO> listEquipment() {
        adminGuard.requireAdmin();
        return equipmentMapper.findAll();
    }

    public Equipment getEquipmentDetail(Long equipmentId) {
        adminGuard.requireAdmin();
        return requireExistingEquipment(equipmentId);
    }

    @Transactional
    public Equipment createEquipment(AdminEquipmentSaveDTO dto) {
        adminGuard.requireAdmin();
        validateGymRoom(dto.getGymRoomId());
        Equipment equipment = new Equipment();
        fillEquipment(equipment, dto);
        equipmentMapper.insert(equipment);
        return getEquipmentDetail(equipment.getId());
    }

    @Transactional
    public Equipment updateEquipment(Long equipmentId, AdminEquipmentSaveDTO dto) {
        adminGuard.requireAdmin();
        Equipment equipment = requireExistingEquipment(equipmentId);
        validateGymRoom(dto.getGymRoomId());
        fillEquipment(equipment, dto);
        equipmentMapper.update(equipment);
        return getEquipmentDetail(equipmentId);
    }

    @Transactional
    public void enableEquipment(Long equipmentId) {
        adminGuard.requireAdmin();
        requireExistingEquipment(equipmentId);
        equipmentMapper.updateStatus(equipmentId, "AVAILABLE");
    }

    @Transactional
    public void disableEquipment(Long equipmentId) {
        adminGuard.requireAdmin();
        requireExistingEquipment(equipmentId);
        equipmentMapper.updateStatus(equipmentId, "DISABLED");
    }

    private Equipment requireExistingEquipment(Long equipmentId) {
        Equipment equipment = equipmentMapper.findById(equipmentId);
        if (equipment == null) {
            throw new BusinessException("equipment does not exist");
        }
        return equipment;
    }

    private void validateGymRoom(Long gymRoomId) {
        if (gymRoomId == null) {
            return;
        }
        if (gymRoomMapper.findById(gymRoomId) == null) {
            throw new BusinessException("gym room does not exist");
        }
    }

    private void fillEquipment(Equipment equipment, AdminEquipmentSaveDTO dto) {
        equipment.setGymRoomId(dto.getGymRoomId());
        equipment.setName(dto.getName());
        equipment.setCategory(dto.getCategory());
        equipment.setBrand(dto.getBrand());
        equipment.setQuantity(dto.getQuantity());
        equipment.setStatus(dto.getStatus());
        equipment.setPurchaseDate(dto.getPurchaseDate());
        equipment.setDescription(dto.getDescription());
    }
}
