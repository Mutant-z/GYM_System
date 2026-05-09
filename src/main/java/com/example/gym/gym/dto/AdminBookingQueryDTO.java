package com.example.gym.gym.dto;

public class AdminBookingQueryDTO {

    private String bookingNo;
    private String memberUsername;
    private Long gymRoomId;
    private String status;

    public String getBookingNo() {
        return bookingNo;
    }

    public void setBookingNo(String bookingNo) {
        this.bookingNo = bookingNo;
    }

    public String getMemberUsername() {
        return memberUsername;
    }

    public void setMemberUsername(String memberUsername) {
        this.memberUsername = memberUsername;
    }

    public Long getGymRoomId() {
        return gymRoomId;
    }

    public void setGymRoomId(Long gymRoomId) {
        this.gymRoomId = gymRoomId;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }
}
