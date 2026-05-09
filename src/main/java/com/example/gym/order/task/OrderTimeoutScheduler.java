package com.example.gym.order.task;

import com.example.gym.order.service.OrderService;
import com.example.gym.order.mapper.OrderMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.beans.factory.annotation.Value;

import java.time.LocalDateTime;

@Component
public class OrderTimeoutScheduler {

    private static final Logger log = LoggerFactory.getLogger(OrderTimeoutScheduler.class);

    private final OrderMapper orderMapper;
    private final OrderService orderService;
    private final long timeoutMinutes;

    public OrderTimeoutScheduler(
            OrderMapper orderMapper,
            OrderService orderService,
            @Value("${gym.order.timeout-minutes:15}") long timeoutMinutes
    ) {
        this.orderMapper = orderMapper;
        this.orderService = orderService;
        this.timeoutMinutes = timeoutMinutes;
    }

    @Scheduled(fixedDelayString = "${gym.order.timeout-scan-interval-ms:60000}")
    public void cancelExpiredUnpaidOrders() {
        LocalDateTime cutoffTime = LocalDateTime.now().minusMinutes(timeoutMinutes);
        int canceledCount = 0;
        for (Long orderId : orderMapper.findExpiredUnpaidOrderIds(cutoffTime)) {
            try {
                if (orderService.cancelUnpaidOrder(orderId)) {
                    canceledCount++;
                }
            } catch (RuntimeException ex) {
                log.warn("failed to auto cancel order {}", orderId, ex);
            }
        }
        if (canceledCount > 0) {
            log.info("auto canceled {} expired unpaid orders before {}", canceledCount, cutoffTime);
        }
    }
}
