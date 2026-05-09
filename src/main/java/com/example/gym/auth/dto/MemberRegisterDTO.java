package com.example.gym.auth.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public class MemberRegisterDTO {

    @NotBlank(message = "username must not be blank")
    @Size(max = 64, message = "username length must not exceed 64")
    private String username;

    @NotBlank(message = "password must not be blank")
    @Size(min = 6, max = 64, message = "password length must be between 6 and 64")
    private String password;

    @NotBlank(message = "nickname must not be blank")
    @Size(max = 64, message = "nickname length must not exceed 64")
    private String nickname;

    @NotBlank(message = "phone must not be blank")
    @Size(max = 20, message = "phone length must not exceed 20")
    private String phone;

    @Email(message = "email format is invalid")
    @Size(max = 128, message = "email length must not exceed 128")
    private String email;

    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public String getNickname() {
        return nickname;
    }

    public void setNickname(String nickname) {
        this.nickname = nickname;
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
}
