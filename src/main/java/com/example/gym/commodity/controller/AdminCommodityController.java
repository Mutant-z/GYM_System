package com.example.gym.commodity.controller;

import com.example.gym.commodity.dto.AdminCommoditySaveDTO;
import com.example.gym.commodity.dto.AdminCommodityStockDTO;
import com.example.gym.commodity.service.AdminCommodityService;
import com.example.gym.commodity.vo.CommodityDetailVO;
import com.example.gym.commodity.vo.CommodityVO;
import com.example.gym.common.api.ApiResponse;
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
@RequestMapping("/admin/commodities")
public class AdminCommodityController {

    private final AdminCommodityService adminCommodityService;

    public AdminCommodityController(AdminCommodityService adminCommodityService) {
        this.adminCommodityService = adminCommodityService;
    }

    @GetMapping
    public ApiResponse<List<CommodityVO>> listCommodities() {
        return ApiResponse.success(adminCommodityService.listCommodities());
    }

    @GetMapping("/{id}")
    public ApiResponse<CommodityDetailVO> getCommodityDetail(@PathVariable("id") Long id) {
        return ApiResponse.success(adminCommodityService.getCommodityDetail(id));
    }

    @PostMapping
    public ApiResponse<CommodityDetailVO> createCommodity(@Valid @RequestBody AdminCommoditySaveDTO dto) {
        return ApiResponse.success(adminCommodityService.createCommodity(dto));
    }

    @PutMapping("/{id}")
    public ApiResponse<CommodityDetailVO> updateCommodity(@PathVariable("id") Long id, @Valid @RequestBody AdminCommoditySaveDTO dto) {
        return ApiResponse.success(adminCommodityService.updateCommodity(id, dto));
    }

    @PostMapping("/{id}/on-sale")
    public ApiResponse<Void> putOnSale(@PathVariable("id") Long id) {
        adminCommodityService.updateCommodityStatus(id, "ON_SALE");
        return ApiResponse.success();
    }

    @PostMapping("/{id}/off-sale")
    public ApiResponse<Void> putOffSale(@PathVariable("id") Long id) {
        adminCommodityService.updateCommodityStatus(id, "OFF_SALE");
        return ApiResponse.success();
    }

    @PostMapping("/{id}/stock")
    public ApiResponse<Void> updateStock(@PathVariable("id") Long id, @Valid @RequestBody AdminCommodityStockDTO dto) {
        adminCommodityService.updateStock(id, dto.getStock());
        return ApiResponse.success();
    }
}
