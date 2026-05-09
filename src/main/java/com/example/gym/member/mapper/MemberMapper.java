package com.example.gym.member.mapper;

import com.example.gym.member.entity.Member;
import com.example.gym.member.vo.AdminMemberDetailVO;
import com.example.gym.member.vo.AdminMemberVO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;
import org.apache.ibatis.annotations.Options;

import java.time.LocalDateTime;
import java.util.List;

@Mapper
public interface MemberMapper {

    @Select("""
            SELECT id, username, password_hash, nickname, real_name, gender, phone, email, birthday,
                   height_cm, weight_kg, fitness_goal, preferred_training_time, injury_notes,
                   membership_status, last_login_at, created_at, updated_at, deleted
            FROM member
            WHERE username = #{username} AND deleted = 0
            LIMIT 1
            """)
    Member findByUsername(String username);

    @Select("""
            SELECT id, username, password_hash, nickname, real_name, gender, phone, email, birthday,
                   height_cm, weight_kg, fitness_goal, preferred_training_time, injury_notes,
                   membership_status, last_login_at, created_at, updated_at, deleted
            FROM member
            WHERE id = #{id}
            LIMIT 1
            """)
    Member findById(@Param("id") Long id);

    @Select("""
            SELECT id, username, password_hash, nickname, real_name, gender, phone, email, birthday,
                   height_cm, weight_kg, fitness_goal, preferred_training_time, injury_notes,
                   membership_status, last_login_at, created_at, updated_at, deleted
            FROM member
            WHERE phone = #{phone}
              AND deleted = 0
            LIMIT 1
            """)
    Member findByPhone(@Param("phone") String phone);

    @Options(useGeneratedKeys = true, keyProperty = "id", keyColumn = "id")
    @Insert("""
            INSERT INTO member (username, password_hash, nickname, real_name, gender, phone, email, birthday,
                                height_cm, weight_kg, fitness_goal, preferred_training_time, injury_notes,
                                membership_status)
            VALUES (#{username}, #{passwordHash}, #{nickname}, #{realName}, #{gender}, #{phone}, #{email}, #{birthday},
                    #{heightCm}, #{weightKg}, #{fitnessGoal}, #{preferredTrainingTime}, #{injuryNotes},
                    #{membershipStatus})
            """)
    int insertMember(Member member);

    @Select("""
            <script>
            SELECT id, username, nickname, real_name, phone, email, membership_status, last_login_at, created_at
            FROM member
            WHERE deleted = 0
            <if test="username != null and username != ''">
              AND username LIKE CONCAT('%', #{username}, '%')
            </if>
            <if test="nickname != null and nickname != ''">
              AND nickname LIKE CONCAT('%', #{nickname}, '%')
            </if>
            <if test="phone != null and phone != ''">
              AND phone LIKE CONCAT('%', #{phone}, '%')
            </if>
            <if test="membershipStatus != null and membershipStatus != ''">
              AND membership_status = #{membershipStatus}
            </if>
            ORDER BY id DESC
            </script>
            """)
    List<AdminMemberVO> findAdminMembers(@Param("username") String username,
                                         @Param("nickname") String nickname,
                                         @Param("phone") String phone,
                                         @Param("membershipStatus") String membershipStatus);

    @Select("""
            SELECT m.id, m.username, m.nickname, m.real_name, m.gender, m.phone, m.email, m.birthday,
                   m.height_cm, m.weight_kg, m.fitness_goal, m.preferred_training_time, m.injury_notes,
                   m.membership_status, m.last_login_at, m.created_at, m.updated_at,
                   (SELECT COUNT(1) FROM gym_booking gb WHERE gb.member_id = m.id AND gb.status = 'CONFIRMED') AS booking_count,
                   (SELECT COUNT(1) FROM course_enrollment ce WHERE ce.member_id = m.id AND ce.status = 'ENROLLED') AS enrolled_course_count,
                   (SELECT COUNT(1) FROM commodity_order co WHERE co.member_id = m.id) AS order_count
            FROM member m
            WHERE m.id = #{id}
              AND m.deleted = 0
            LIMIT 1
            """)
    AdminMemberDetailVO findAdminMemberDetail(@Param("id") Long id);

    @Update("""
            UPDATE member
            SET last_login_at = #{lastLoginAt}
            WHERE id = #{id}
            """)
    int updateLastLoginAt(@Param("id") Long id, @Param("lastLoginAt") LocalDateTime lastLoginAt);

    @Update("""
            UPDATE member
            SET nickname = #{nickname},
                real_name = #{realName},
                gender = #{gender},
                phone = #{phone},
                email = #{email},
                birthday = #{birthday},
                height_cm = #{heightCm},
                weight_kg = #{weightKg},
                fitness_goal = #{fitnessGoal},
                preferred_training_time = #{preferredTrainingTime},
                injury_notes = #{injuryNotes}
            WHERE id = #{id}
            """)
    int updateAdminMember(Member member);

    @Update("""
            UPDATE member
            SET nickname = #{nickname},
                real_name = #{realName},
                gender = #{gender},
                phone = #{phone},
                email = #{email},
                birthday = #{birthday},
                height_cm = #{heightCm},
                weight_kg = #{weightKg},
                fitness_goal = #{fitnessGoal},
                preferred_training_time = #{preferredTrainingTime},
                injury_notes = #{injuryNotes}
            WHERE id = #{id}
              AND deleted = 0
            """)
    int updateMemberProfile(Member member);

    @Update("""
            UPDATE member
            SET membership_status = #{status}
            WHERE id = #{id}
            """)
    int updateMembershipStatus(@Param("id") Long id, @Param("status") String status);
}
