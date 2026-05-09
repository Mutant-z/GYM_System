package com.example.gym.equipment.controller;

import com.example.gym.common.api.ApiResponse;
import com.example.gym.equipment.dto.AdminEquipmentSaveDTO;
import com.example.gym.equipment.entity.Equipment;
import com.example.gym.equipment.service.AdminEquipmentService;
import com.example.gym.equipment.vo.EquipmentVO;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/admin/equipments")
public class AdminEquipmentController {

    private final AdminEquipmentService adminEquipmentService;

    public AdminEquipmentController(AdminEquipmentService adminEquipmentService) {
        this.adminEquipmentService = adminEquipmentService;
    }

    @GetMapping
    public ApiResponse<List<EquipmentVO>> listEquipment() {
        return ApiResponse.success(adminEquipmentService.listEquipment());
    }

    @GetMapping("/{id}")
    public ApiResponse<Equipment> getEquipmentDetail(@PathVariable("id") Long id) {
        return ApiResponse.success(adminEquipmentService.getEquipmentDetail(id));
    }

    @PostMapping
    public ApiResponse<Equipment> createEquipment(@Valid @RequestBody AdminEquipmentSaveDTO dto) {
        return ApiResponse.success(adminEquipmentService.createEquipment(dto));
    }

    @PutMapping("/{id}")
    public ApiResponse<Equipment> updateEquipment(@PathVariable("id") Long id, @Valid @RequestBody AdminEquipmentSaveDTO dto) {
        return ApiResponse.success(adminEquipmentService.updateEquipment(id, dto));
    }

    @PostMapping("/{id}/enable")
    public ApiResponse<Void> enableEquipment(@PathVariable("id") Long id) {
        adminEquipmentService.enableEquipment(id);
        return ApiResponse.success();
    }

    @PostMapping("/{id}/disable")
    public ApiResponse<Void> disableEquipment(@PathVariable("id") Long id) {
        adminEquipmentService.disableEquipment(id);
        return ApiResponse.success();
    }
}
