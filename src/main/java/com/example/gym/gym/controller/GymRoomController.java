package com.example.gym.gym.controller;

import com.example.gym.common.api.ApiResponse;
import com.example.gym.gym.service.GymRoomService;
import com.example.gym.gym.vo.GymRoomDetailVO;
import com.example.gym.gym.vo.GymRoomVO;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/gym/rooms")
public class GymRoomController {

    private final GymRoomService gymRoomService;

    public GymRoomController(GymRoomService gymRoomService) {
        this.gymRoomService = gymRoomService;
    }

    @GetMapping
    public ApiResponse<List<GymRoomVO>> listRooms() {
        return ApiResponse.success(gymRoomService.listRooms());
    }

    @GetMapping("/{id}")
    public ApiResponse<GymRoomDetailVO> getRoomDetail(@PathVariable Long id) {
        return ApiResponse.success(gymRoomService.getRoomDetail(id));
    }
}
