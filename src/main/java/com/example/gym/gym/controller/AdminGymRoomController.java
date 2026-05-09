package com.example.gym.gym.controller;

import com.example.gym.common.api.ApiResponse;
import com.example.gym.gym.dto.AdminGymRoomSaveDTO;
import com.example.gym.gym.service.AdminGymRoomService;
import com.example.gym.gym.vo.GymRoomDetailVO;
import com.example.gym.gym.vo.GymRoomVO;
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
@RequestMapping("/admin/gym/rooms")
public class AdminGymRoomController {

    private final AdminGymRoomService adminGymRoomService;

    public AdminGymRoomController(AdminGymRoomService adminGymRoomService) {
        this.adminGymRoomService = adminGymRoomService;
    }

    @GetMapping
    public ApiResponse<List<GymRoomVO>> listRooms() {
        return ApiResponse.success(adminGymRoomService.listRooms());
    }

    @GetMapping("/{id}")
    public ApiResponse<GymRoomDetailVO> getRoomDetail(@PathVariable("id") Long id) {
        return ApiResponse.success(adminGymRoomService.getRoomDetail(id));
    }

    @PostMapping
    public ApiResponse<GymRoomDetailVO> createRoom(@Valid @RequestBody AdminGymRoomSaveDTO dto) {
        return ApiResponse.success(adminGymRoomService.createRoom(dto));
    }

    @PutMapping("/{id}")
    public ApiResponse<GymRoomDetailVO> updateRoom(@PathVariable("id") Long id, @Valid @RequestBody AdminGymRoomSaveDTO dto) {
        return ApiResponse.success(adminGymRoomService.updateRoom(id, dto));
    }

    @PostMapping("/{id}/enable")
    public ApiResponse<Void> enableRoom(@PathVariable("id") Long id) {
        adminGymRoomService.enableRoom(id);
        return ApiResponse.success();
    }

    @PostMapping("/{id}/disable")
    public ApiResponse<Void> disableRoom(@PathVariable("id") Long id) {
        adminGymRoomService.disableRoom(id);
        return ApiResponse.success();
    }
}
