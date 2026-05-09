package com.example.gym.admin.mapper;

import com.example.gym.admin.entity.Admin;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.time.LocalDateTime;

@Mapper
public interface AdminMapper {

    @Select("""
            SELECT id, username, password_hash, name, phone, role, status,
                   last_login_at, created_at, updated_at
            FROM admin
            WHERE username = #{username}
            LIMIT 1
            """)
    Admin findByUsername(String username);

    @Update("""
            UPDATE admin
            SET last_login_at = #{lastLoginAt}
            WHERE id = #{id}
            """)
    int updateLastLoginAt(@Param("id") Long id, @Param("lastLoginAt") LocalDateTime lastLoginAt);
}
