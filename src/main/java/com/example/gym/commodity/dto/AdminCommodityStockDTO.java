package com.example.gym.commodity.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;

public class AdminCommodityStockDTO {

    @NotNull(message = "stock must not be null")
    @Min(value = 0, message = "stock must not be negative")
    private Integer stock;

    public Integer getStock() {
        return stock;
    }

    public void setStock(Integer stock) {
        this.stock = stock;
    }
}
