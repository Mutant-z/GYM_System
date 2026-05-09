package com.example.gym.commodity.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.math.BigDecimal;

public class AdminCommoditySaveDTO {

    @NotBlank(message = "name must not be blank")
    @Size(max = 128, message = "name length must not exceed 128")
    private String name;

    @Size(max = 64, message = "category length must not exceed 64")
    private String category;

    @NotNull(message = "price must not be null")
    @DecimalMin(value = "0.00", message = "price must not be negative")
    private BigDecimal price;

    @NotNull(message = "stock must not be null")
    @Min(value = 0, message = "stock must not be negative")
    private Integer stock;

    @Size(max = 255, message = "coverImage length must not exceed 255")
    private String coverImage;

    @Size(max = 500, message = "description length must not exceed 500")
    private String description;

    @NotBlank(message = "status must not be blank")
    @Size(max = 32, message = "status length must not exceed 32")
    private String status;

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

    public BigDecimal getPrice() {
        return price;
    }

    public void setPrice(BigDecimal price) {
        this.price = price;
    }

    public Integer getStock() {
        return stock;
    }

    public void setStock(Integer stock) {
        this.stock = stock;
    }

    public String getCoverImage() {
        return coverImage;
    }

    public void setCoverImage(String coverImage) {
        this.coverImage = coverImage;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }
}
