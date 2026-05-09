package com.example.gym.gym.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.time.LocalTime;

public class AdminGymRoomSaveDTO {

    @NotBlank(message = "name must not be blank")
    @Size(max = 128, message = "name length must not exceed 128")
    private String name;

    @Size(max = 255, message = "location length must not exceed 255")
    private String location;

    @NotNull(message = "capacity must not be null")
    @Min(value = 1, message = "capacity must be greater than 0")
    private Integer capacity;

    private LocalTime openTime;

    private LocalTime closeTime;

    @NotBlank(message = "status must not be blank")
    @Size(max = 32, message = "status length must not exceed 32")
    private String status;

    @Size(max = 500, message = "description length must not exceed 500")
    private String description;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getLocation() {
        return location;
    }

    public void setLocation(String location) {
        this.location = location;
    }

    public Integer getCapacity() {
        return capacity;
    }

    public void setCapacity(Integer capacity) {
        this.capacity = capacity;
    }

    public LocalTime getOpenTime() {
        return openTime;
    }

    public void setOpenTime(LocalTime openTime) {
        this.openTime = openTime;
    }

    public LocalTime getCloseTime() {
        return closeTime;
    }

    public void setCloseTime(LocalTime closeTime) {
        this.closeTime = closeTime;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }
}
