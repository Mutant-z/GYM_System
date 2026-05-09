package com.example.gym.order.vo;

import java.util.List;

public class OrderDetailVO extends OrderVO {

    private List<OrderItemVO> items;

    public List<OrderItemVO> getItems() {
        return items;
    }

    public void setItems(List<OrderItemVO> items) {
        this.items = items;
    }
}
