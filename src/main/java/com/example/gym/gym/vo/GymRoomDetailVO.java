package com.example.gym.gym.vo;

public class GymRoomDetailVO extends GymRoomVO {

    private Integer todayBookedHeadCount;
    private Boolean bookable;

    public Integer getTodayBookedHeadCount() {
        return todayBookedHeadCount;
    }

    public void setTodayBookedHeadCount(Integer todayBookedHeadCount) {
        this.todayBookedHeadCount = todayBookedHeadCount;
    }

    public Boolean getBookable() {
        return bookable;
    }

    public void setBookable(Boolean bookable) {
        this.bookable = bookable;
    }
}
