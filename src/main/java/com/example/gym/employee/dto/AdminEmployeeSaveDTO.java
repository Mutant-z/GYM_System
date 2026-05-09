package com.example.gym.employee.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

import java.time.LocalDate;

public class AdminEmployeeSaveDTO {

    @NotBlank(message = "name must not be blank")
    @Size(max = 64, message = "name length must not exceed 64")
    private String name;

    @Size(max = 20, message = "phone length must not exceed 20")
    private String phone;

    @Size(max = 16, message = "gender length must not exceed 16")
    private String gender;

    @NotBlank(message = "position must not be blank")
    @Size(max = 32, message = "position length must not exceed 32")
    private String position;

    @Size(max = 255, message = "specialty length must not exceed 255")
    private String specialty;

    private LocalDate hireDate;

    @NotBlank(message = "status must not be blank")
    @Size(max = 32, message = "status length must not exceed 32")
    private String status;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getPhone() {
        return phone;
    }

    public void setPhone(String phone) {
        this.phone = phone;
    }

    public String getGender() {
        return gender;
    }

    public void setGender(String gender) {
        this.gender = gender;
    }

    public String getPosition() {
        return position;
    }

    public void setPosition(String position) {
        this.position = position;
    }

    public String getSpecialty() {
        return specialty;
    }

    public void setSpecialty(String specialty) {
        this.specialty = specialty;
    }

    public LocalDate getHireDate() {
        return hireDate;
    }

    public void setHireDate(LocalDate hireDate) {
        this.hireDate = hireDate;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }
}
