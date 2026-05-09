package com.example.gym.order.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Size;

import java.util.List;

public class CreateOrderDTO {

    @NotEmpty(message = "cartItemIds must not be empty")
    private List<Long> cartItemIds;

    @NotBlank(message = "receiverName must not be blank")
    @Size(max = 64, message = "receiverName length must not exceed 64")
    private String receiverName;

    @NotBlank(message = "receiverPhone must not be blank")
    @Size(max = 20, message = "receiverPhone length must not exceed 20")
    private String receiverPhone;

    @NotBlank(message = "receiverAddress must not be blank")
    @Size(max = 255, message = "receiverAddress length must not exceed 255")
    private String receiverAddress;

    public List<Long> getCartItemIds() {
        return cartItemIds;
    }

    public void setCartItemIds(List<Long> cartItemIds) {
        this.cartItemIds = cartItemIds;
    }

    public String getReceiverName() {
        return receiverName;
    }

    public void setReceiverName(String receiverName) {
        this.receiverName = receiverName;
    }

    public String getReceiverPhone() {
        return receiverPhone;
    }

    public void setReceiverPhone(String receiverPhone) {
        this.receiverPhone = receiverPhone;
    }

    public String getReceiverAddress() {
        return receiverAddress;
    }

    public void setReceiverAddress(String receiverAddress) {
        this.receiverAddress = receiverAddress;
    }
}
