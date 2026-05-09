package com.example.gym.commodity.controller;

import com.example.gym.commodity.service.CommodityService;
import com.example.gym.commodity.vo.CommodityDetailVO;
import com.example.gym.commodity.vo.CommodityVO;
import com.example.gym.common.api.ApiResponse;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/commodities")
public class CommodityController {

    private final CommodityService commodityService;

    public CommodityController(CommodityService commodityService) {
        this.commodityService = commodityService;
    }

    @GetMapping
    public ApiResponse<List<CommodityVO>> listCommodities() {
        return ApiResponse.success(commodityService.listCommodities());
    }

    @GetMapping("/{id}")
    public ApiResponse<CommodityDetailVO> getCommodityDetail(@PathVariable Long id) {
        return ApiResponse.success(commodityService.getCommodityDetail(id));
    }
}
