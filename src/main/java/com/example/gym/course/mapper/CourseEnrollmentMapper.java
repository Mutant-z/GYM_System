package com.example.gym.course.mapper;

import com.example.gym.course.entity.CourseEnrollment;
import com.example.gym.course.vo.AdminCourseEnrollmentVO;
import com.example.gym.course.vo.MyCourseVO;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.util.List;

@Mapper
public interface CourseEnrollmentMapper {

    @Select("""
            SELECT id, enrollment_no, member_id, course_id, status, created_at, updated_at
            FROM course_enrollment
            WHERE member_id = #{memberId} AND course_id = #{courseId}
            LIMIT 1
            """)
    CourseEnrollment findByMemberIdAndCourseId(@Param("memberId") Long memberId, @Param("courseId") Long courseId);

    @Insert("""
            INSERT INTO course_enrollment (enrollment_no, member_id, course_id, status)
            VALUES (#{enrollmentNo}, #{memberId}, #{courseId}, #{status})
            """)
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(CourseEnrollment enrollment);

    @Update("""
            UPDATE course_enrollment
            SET status = #{status}
            WHERE id = #{id}
            """)
    int updateStatus(@Param("id") Long id, @Param("status") String status);

    @Select("""
            SELECT COUNT(1)
            FROM course_enrollment
            WHERE course_id = #{courseId}
              AND status = 'ENROLLED'
            """)
    int countEnrolledByCourseId(@Param("courseId") Long courseId);

    @Select("""
            SELECT ce.id AS enrollment_id, ce.enrollment_no, ce.status AS enrollment_status,
                   c.id AS course_id, c.name AS course_name, c.course_type,
                   e.name AS coach_name, gr.name AS gym_room_name,
                   c.start_time, c.end_time, c.price, ce.created_at
            FROM course_enrollment ce
            JOIN course c ON c.id = ce.course_id
            LEFT JOIN employee e ON e.id = c.coach_id
            LEFT JOIN gym_room gr ON gr.id = c.gym_room_id
            WHERE ce.member_id = #{memberId}
              AND (#{status} IS NULL OR #{status} = '' OR ce.status = #{status})
            ORDER BY ce.created_at DESC, ce.id DESC
            """)
    List<MyCourseVO> findMyCourses(@Param("memberId") Long memberId, @Param("status") String status);

    @Select("""
            SELECT id, enrollment_no, member_id, course_id, status, created_at, updated_at
            FROM course_enrollment
            WHERE id = #{id}
            LIMIT 1
            """)
    CourseEnrollment findById(@Param("id") Long id);

    @Select("""
            SELECT ce.id AS enrollment_id, ce.enrollment_no, ce.status AS enrollment_status,
                   m.id AS member_id, m.username AS member_username, m.nickname AS member_display_name,
                   c.id AS course_id, c.name AS course_name, c.course_type,
                   e.name AS coach_name, gr.name AS gym_room_name,
                   c.start_time, c.end_time, c.price, ce.created_at
            FROM course_enrollment ce
            JOIN member m ON m.id = ce.member_id
            JOIN course c ON c.id = ce.course_id
            LEFT JOIN employee e ON e.id = c.coach_id
            LEFT JOIN gym_room gr ON gr.id = c.gym_room_id
            WHERE (#{enrollmentNo} IS NULL OR #{enrollmentNo} = '' OR ce.enrollment_no = #{enrollmentNo})
              AND (#{memberUsername} IS NULL OR #{memberUsername} = '' OR m.username = #{memberUsername})
              AND (#{courseId} IS NULL OR ce.course_id = #{courseId})
              AND (#{status} IS NULL OR #{status} = '' OR ce.status = #{status})
            ORDER BY ce.created_at DESC, ce.id DESC
            """)
    List<AdminCourseEnrollmentVO> findAllEnrollments(
            @Param("enrollmentNo") String enrollmentNo,
            @Param("memberUsername") String memberUsername,
            @Param("courseId") Long courseId,
            @Param("status") String status
    );
}
