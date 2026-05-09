package com.example.gym.gym.mapper;

import com.example.gym.gym.entity.GymBooking;
import com.example.gym.gym.vo.GymBookingVO;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.time.LocalDateTime;
import java.util.List;

@Mapper
public interface GymBookingMapper {

    @Insert("""
            INSERT INTO gym_booking (
                booking_no, member_id, gym_room_id, booking_date, start_time, end_time,
                duration_minutes, head_count, status, remark
            ) VALUES (
                #{bookingNo}, #{memberId}, #{gymRoomId}, #{bookingDate}, #{startTime}, #{endTime},
                #{durationMinutes}, #{headCount}, #{status}, #{remark}
            )
            """)
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(GymBooking booking);

    @Select("""
            SELECT COUNT(1)
            FROM gym_booking
            WHERE member_id = #{memberId}
              AND status = 'CONFIRMED'
              AND start_time < #{endTime}
              AND end_time > #{startTime}
            """)
    int countMemberBookingConflicts(
            @Param("memberId") Long memberId,
            @Param("startTime") LocalDateTime startTime,
            @Param("endTime") LocalDateTime endTime
    );

    @Select("""
            SELECT COALESCE(SUM(head_count), 0)
            FROM gym_booking
            WHERE gym_room_id = #{gymRoomId}
              AND status = 'CONFIRMED'
              AND start_time < #{endTime}
              AND end_time > #{startTime}
            """)
    Integer sumRoomBookedHeadCountInRange(
            @Param("gymRoomId") Long gymRoomId,
            @Param("startTime") LocalDateTime startTime,
            @Param("endTime") LocalDateTime endTime
    );

    @Select("""
            SELECT gb.id, gb.booking_no, gb.member_id, m.username AS member_username, m.nickname AS member_display_name,
                   gb.gym_room_id, gr.name AS gym_room_name, gb.booking_date,
                   gb.start_time, gb.end_time, gb.duration_minutes, gb.head_count,
                   gb.status, gb.remark, gb.created_at
            FROM gym_booking gb
            JOIN gym_room gr ON gr.id = gb.gym_room_id
            JOIN member m ON m.id = gb.member_id
            WHERE gb.member_id = #{memberId}
              AND (#{status} IS NULL OR #{status} = '' OR gb.status = #{status})
            ORDER BY gb.created_at DESC, gb.id DESC
            """)
    List<GymBookingVO> findMyBookings(@Param("memberId") Long memberId, @Param("status") String status);

    @Select("""
            SELECT gb.id, gb.booking_no, gb.member_id, m.username AS member_username, m.nickname AS member_display_name,
                   gb.gym_room_id, gr.name AS gym_room_name, gb.booking_date,
                   gb.start_time, gb.end_time, gb.duration_minutes, gb.head_count,
                   gb.status, gb.remark, gb.created_at
            FROM gym_booking gb
            JOIN gym_room gr ON gr.id = gb.gym_room_id
            JOIN member m ON m.id = gb.member_id
            WHERE (#{bookingNo} IS NULL OR #{bookingNo} = '' OR gb.booking_no = #{bookingNo})
              AND (#{memberUsername} IS NULL OR #{memberUsername} = '' OR m.username = #{memberUsername})
              AND (#{gymRoomId} IS NULL OR gb.gym_room_id = #{gymRoomId})
              AND (#{status} IS NULL OR #{status} = '' OR gb.status = #{status})
            ORDER BY gb.created_at DESC, gb.id DESC
            """)
    List<GymBookingVO> findAllBookings(
            @Param("bookingNo") String bookingNo,
            @Param("memberUsername") String memberUsername,
            @Param("gymRoomId") Long gymRoomId,
            @Param("status") String status
    );

    @Select("""
            SELECT id, booking_no, member_id, gym_room_id, booking_date, start_time, end_time,
                   duration_minutes, head_count, status, remark, created_at, updated_at
            FROM gym_booking
            WHERE id = #{id}
            LIMIT 1
            """)
    GymBooking findById(@Param("id") Long id);

    @Update("""
            UPDATE gym_booking
            SET status = 'CANCELED'
            WHERE id = #{id}
            """)
    int cancelById(@Param("id") Long id);
}
