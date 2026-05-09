package com.example.gym.gym.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.time.LocalDateTime;

public class CreateGymBookingDTO {

    @NotNull(message = "gymRoomId must not be null")
    private Long gymRoomId;

    @NotNull(message = "startTime must not be null")
    private LocalDateTime startTime;

    @NotNull(message = "endTime must not be null")
    private LocalDateTime endTime;

    @NotNull(message = "headCount must not be null")
    @Min(value = 1, message = "headCount must be greater than or equal to 1")
    private Integer headCount;

    @Size(max = 255, message = "remark length must not exceed 255")
    private String remark;

    public Long getGymRoomId() {
        return gymRoomId;
    }

    public void setGymRoomId(Long gymRoomId) {
        this.gymRoomId = gymRoomId;
    }

    public LocalDateTime getStartTime() {
        return startTime;
    }

    public void setStartTime(LocalDateTime startTime) {
        this.startTime = startTime;
    }

    public LocalDateTime getEndTime() {
        return endTime;
    }

    public void setEndTime(LocalDateTime endTime) {
        this.endTime = endTime;
    }

    public Integer getHeadCount() {
        return headCount;
    }

    public void setHeadCount(Integer headCount) {
        this.headCount = headCount;
    }

    public String getRemark() {
        return remark;
    }

    public void setRemark(String remark) {
        this.remark = remark;
    }
}
