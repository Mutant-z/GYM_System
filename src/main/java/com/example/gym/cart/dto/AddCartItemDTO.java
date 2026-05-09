package com.example.gym.cart.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;

public class AddCartItemDTO {

    @NotNull(message = "commodityId must not be null")
    private Long commodityId;

    @NotNull(message = "quantity must not be null")
    @Min(value = 1, message = "quantity must be greater than or equal to 1")
    private Integer quantity;

    public Long getCommodityId() {
        return commodityId;
    }

    public void setCommodityId(Long commodityId) {
        this.commodityId = commodityId;
    }

    public Integer getQuantity() {
        return quantity;
    }

    public void setQuantity(Integer quantity) {
        this.quantity = quantity;
    }
}
