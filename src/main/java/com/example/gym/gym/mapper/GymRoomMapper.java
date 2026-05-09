package com.example.gym.gym.mapper;

import com.example.gym.gym.entity.GymRoom;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.time.LocalDate;
import java.util.List;

@Mapper
public interface GymRoomMapper {

    @Select("""
            SELECT id, name, location, capacity, open_time, close_time, status, description, created_at, updated_at
            FROM gym_room
            ORDER BY id DESC
            """)
    List<GymRoom> findAll();

    @Select("""
            SELECT id, name, location, capacity, open_time, close_time, status, description, created_at, updated_at
            FROM gym_room
            WHERE id = #{id}
            LIMIT 1
            """)
    GymRoom findById(@Param("id") Long id);

    @Select("""
            SELECT id, name, location, capacity, open_time, close_time, status, description, created_at, updated_at
            FROM gym_room
            WHERE name = #{name}
            LIMIT 1
            """)
    GymRoom findByName(@Param("name") String name);

    @Select("""
            SELECT COALESCE(SUM(head_count), 0)
            FROM gym_booking
            WHERE gym_room_id = #{gymRoomId}
              AND booking_date = #{bookingDate}
              AND status = 'CONFIRMED'
            """)
    Integer sumTodayBookedHeadCount(@Param("gymRoomId") Long gymRoomId, @Param("bookingDate") LocalDate bookingDate);

    @Insert("""
            INSERT INTO gym_room (name, location, capacity, open_time, close_time, status, description)
            VALUES (#{name}, #{location}, #{capacity}, #{openTime}, #{closeTime}, #{status}, #{description})
            """)
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(GymRoom gymRoom);

    @Update("""
            UPDATE gym_room
            SET name = #{name},
                location = #{location},
                capacity = #{capacity},
                open_time = #{openTime},
                close_time = #{closeTime},
                status = #{status},
                description = #{description}
            WHERE id = #{id}
            """)
    int update(GymRoom gymRoom);

    @Update("""
            UPDATE gym_room
            SET status = #{status}
            WHERE id = #{id}
            """)
    int updateStatus(@Param("id") Long id, @Param("status") String status);
}
