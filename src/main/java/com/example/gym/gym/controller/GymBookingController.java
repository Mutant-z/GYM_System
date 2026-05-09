package com.example.gym.gym.controller;

import com.example.gym.common.api.ApiResponse;
import com.example.gym.gym.dto.AdminBookingQueryDTO;
import com.example.gym.gym.dto.CreateGymBookingDTO;
import com.example.gym.gym.dto.MyBookingQueryDTO;
import com.example.gym.gym.service.GymBookingService;
import com.example.gym.gym.vo.GymBookingVO;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/gym/bookings")
public class GymBookingController {

    private final GymBookingService gymBookingService;

    public GymBookingController(GymBookingService gymBookingService) {
        this.gymBookingService = gymBookingService;
    }

    @PostMapping
    public ApiResponse<GymBookingVO> createBooking(@Valid @RequestBody CreateGymBookingDTO dto) {
        return ApiResponse.success(gymBookingService.createBooking(dto));
    }

    @GetMapping("/me")
    public ApiResponse<List<GymBookingVO>> listMyBookings(@RequestParam(value = "status", required = false) String status) {
        MyBookingQueryDTO queryDTO = new MyBookingQueryDTO();
        queryDTO.setStatus(status);
        return ApiResponse.success(gymBookingService.listMyBookings(queryDTO));
    }

    @GetMapping
    public ApiResponse<List<GymBookingVO>> listAllBookings(
            @RequestParam(value = "bookingNo", required = false) String bookingNo,
            @RequestParam(value = "memberUsername", required = false) String memberUsername,
            @RequestParam(value = "gymRoomId", required = false) Long gymRoomId,
            @RequestParam(value = "status", required = false) String status
    ) {
        AdminBookingQueryDTO queryDTO = new AdminBookingQueryDTO();
        queryDTO.setBookingNo(bookingNo);
        queryDTO.setMemberUsername(memberUsername);
        queryDTO.setGymRoomId(gymRoomId);
        queryDTO.setStatus(status);
        return ApiResponse.success(gymBookingService.listAllBookings(queryDTO));
    }

    @PostMapping("/{id}/cancel")
    public ApiResponse<Void> cancelBooking(@PathVariable Long id) {
        gymBookingService.cancelBooking(id);
        return ApiResponse.success();
    }

    @PostMapping("/{id}/admin-cancel")
    public ApiResponse<Void> adminCancelBooking(@PathVariable Long id) {
        gymBookingService.adminCancelBooking(id);
        return ApiResponse.success();
    }
}
