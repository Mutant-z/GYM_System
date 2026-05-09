package com.example.gym.equipment.vo;

import java.time.LocalDate;
import java.time.LocalDateTime;

public class EquipmentVO {

    private Long id;
    private Long gymRoomId;
    private String gymRoomName;
    private String name;
    private String category;
    private String brand;
    private Integer quantity;
    private String status;
    private LocalDate purchaseDate;
    private String description;
    private LocalDateTime createdAt;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Long getGymRoomId() {
        return gymRoomId;
    }

    public void setGymRoomId(Long gymRoomId) {
        this.gymRoomId = gymRoomId;
    }

    public String getGymRoomName() {
        return gymRoomName;
    }

    public void setGymRoomName(String gymRoomName) {
        this.gymRoomName = gymRoomName;
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

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }
}
