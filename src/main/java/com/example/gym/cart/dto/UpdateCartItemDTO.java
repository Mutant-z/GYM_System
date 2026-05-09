package com.example.gym.cart.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;

public class UpdateCartItemDTO {

    @NotNull(message = "quantity must not be null")
    @Min(value = 1, message = "quantity must be greater than or equal to 1")
    private Integer quantity;

    @NotNull(message = "selected must not be null")
    private Boolean selected;

    public Integer getQuantity() {
        return quantity;
    }

    public void setQuantity(Integer quantity) {
        this.quantity = quantity;
    }

    public Boolean getSelected() {
        return selected;
    }

    public void setSelected(Boolean selected) {
        this.selected = selected;
    }
}
