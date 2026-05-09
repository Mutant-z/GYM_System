package com.example.gym.equipment.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.time.LocalDate;

public class AdminEquipmentSaveDTO {

    private Long gymRoomId;

    @NotBlank(message = "name must not be blank")
    @Size(max = 128, message = "name length must not exceed 128")
    private String name;

    @Size(max = 64, message = "category length must not exceed 64")
    private String category;

    @Size(max = 64, message = "brand length must not exceed 64")
    private String brand;

    @NotNull(message = "quantity must not be null")
    @Min(value = 1, message = "quantity must be greater than 0")
    private Integer quantity;

    @NotBlank(message = "status must not be blank")
    @Size(max = 32, message = "status length must not exceed 32")
    private String status;

    private LocalDate purchaseDate;

    @Size(max = 500, message = "description length must not exceed 500")
    private String description;

    public Long getGymRoomId() {
        return gymRoomId;
    }

    public void setGymRoomId(Long gymRoomId) {
        this.gymRoomId = gymRoomId;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getCategory() {
        return category;
    }

    public void setCategory(String category) {
        this.category = category;
    }

    public String getBrand() {
        return brand;
    }

    public void setBrand(String brand) {
        this.brand = brand;
    }

    public Integer getQuantity() {
        return quantity;
    }

    public void setQuantity(Integer quantity) {
        this.quantity = quantity;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public LocalDate getPurchaseDate() {
        return purchaseDate;
    }

    public void setPurchaseDate(LocalDate purchaseDate) {
        this.purchaseDate = purchaseDate;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }
}
