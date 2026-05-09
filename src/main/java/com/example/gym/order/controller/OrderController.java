package com.example.gym.order.controller;

import com.example.gym.common.api.ApiResponse;
import com.example.gym.order.dto.CreateOrderDTO;
import com.example.gym.order.service.OrderService;
import com.example.gym.order.vo.OrderDetailVO;
import com.example.gym.order.vo.OrderVO;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/orders")
public class OrderController {

    private static final Logger log = LoggerFactory.getLogger(OrderController.class);

    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    @PostMapping
    public ApiResponse<OrderDetailVO> createOrder(@Valid @RequestBody CreateOrderDTO dto) {
        return ApiResponse.success(orderService.createOrder(dto));
    }

    @GetMapping
    public ApiResponse<List<OrderVO>> listOrders() {
        log.info("OrderController.listOrders entered");
        return ApiResponse.success(orderService.listOrders());
    }

    @GetMapping("/{id}")
    public ApiResponse<OrderDetailVO> getOrderDetail(@PathVariable Long id) {
        return ApiResponse.success(orderService.getOrderDetail(id));
    }

    @RequestMapping(
            value = {"/{id}/cancel", "/{id}/cancel/", "/cancel/{id}"},
            method = {RequestMethod.POST, RequestMethod.PUT, RequestMethod.PATCH}
    )
    public ApiResponse<Void> cancelOrder(@PathVariable Long id) {
        orderService.cancelOrder(id);
        return ApiResponse.success();
    }
}
