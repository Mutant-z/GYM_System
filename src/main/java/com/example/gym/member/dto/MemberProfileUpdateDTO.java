package com.example.gym.member.dto;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

import java.time.LocalDate;

public class MemberProfileUpdateDTO {

    @NotBlank(message = "nickname must not be blank")
    @Size(max = 64, message = "nickname length must not exceed 64")
    private String nickname;

    @Size(max = 64, message = "realName length must not exceed 64")
    private String realName;

    @Size(max = 16, message = "gender length must not exceed 16")
    private String gender;

    @NotBlank(message = "phone must not be blank")
    @Size(max = 20, message = "phone length must not exceed 20")
    private String phone;

    @Email(message = "email format is invalid")
    @Size(max = 128, message = "email length must not exceed 128")
    private String email;

    private LocalDate birthday;

    @DecimalMin(value = "1.0", message = "heightCm must be greater than 0")
    @DecimalMax(value = "300.0", message = "heightCm is too large")
    private Double heightCm;

    @DecimalMin(value = "1.0", message = "weightKg must be greater than 0")
    @DecimalMax(value = "500.0", message = "weightKg is too large")
    private Double weightKg;

    @Size(max = 255, message = "fitnessGoal length must not exceed 255")
    private String fitnessGoal;

    @Size(max = 64, message = "preferredTrainingTime length must not exceed 64")
    private String preferredTrainingTime;

    @Size(max = 255, message = "injuryNotes length must not exceed 255")
    private String injuryNotes;

    public String getNickname() {
        return nickname;
    }

    public void setNickname(String nickname) {
        this.nickname = nickname;
    }

    public String getRealName() {
        return realName;
    }

    public void setRealName(String realName) {
        this.realName = realName;
    }

    public String getGender() {
        return gender;
    }

    public void setGender(String gender) {
        this.gender = gender;
    }

    public String getPhone() {
        return phone;
    }

    public void setPhone(String phone) {
        this.phone = phone;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public LocalDate getBirthday() {
        return birthday;
    }

    public void setBirthday(LocalDate birthday) {
        this.birthday = birthday;
    }

    public Double getHeightCm() {
        return heightCm;
    }

    public void setHeightCm(Double heightCm) {
        this.heightCm = heightCm;
    }

    public Double getWeightKg() {
        return weightKg;
    }

    public void setWeightKg(Double weightKg) {
        this.weightKg = weightKg;
    }

    public String getFitnessGoal() {
        return fitnessGoal;
    }

    public void setFitnessGoal(String fitnessGoal) {
        this.fitnessGoal = fitnessGoal;
    }

    public String getPreferredTrainingTime() {
        return preferredTrainingTime;
    }

    public void setPreferredTrainingTime(String preferredTrainingTime) {
        this.preferredTrainingTime = preferredTrainingTime;
    }

    public String getInjuryNotes() {
        return injuryNotes;
    }

    public void setInjuryNotes(String injuryNotes) {
        this.injuryNotes = injuryNotes;
    }
}
