package com.example.gym.course.mapper;

import com.example.gym.course.entity.Course;
import com.example.gym.course.vo.CourseVO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.util.List;

@Mapper
public interface CourseMapper {

    @Select("""
            SELECT c.id, c.name, c.course_type, c.coach_id, e.name AS coach_name, c.gym_room_id,
                   gr.name AS gym_room_name, c.start_time, c.end_time, c.capacity,
                   COALESCE((
                       SELECT COUNT(1)
                       FROM course_enrollment ce
                       WHERE ce.course_id = c.id AND ce.status = 'ENROLLED'
                   ), 0) AS enrolled_count,
                   c.price, c.description, c.status
            FROM course c
            LEFT JOIN employee e ON e.id = c.coach_id
            LEFT JOIN gym_room gr ON gr.id = c.gym_room_id
            WHERE (#{status} IS NULL OR #{status} = '' OR c.status = #{status})
            ORDER BY c.start_time ASC, c.id DESC
            """)
    List<CourseVO> findCourses(@Param("status") String status);

    @Select("""
            SELECT id, name, coach_id, gym_room_id, course_type, start_time, end_time,
                   capacity, price, description, status, created_at, updated_at
            FROM course
            WHERE id = #{id}
            LIMIT 1
            """)
    Course findById(@Param("id") Long id);

    @Select("""
            SELECT c.id, c.name, c.course_type, c.coach_id, e.name AS coach_name, c.gym_room_id,
                   gr.name AS gym_room_name, c.start_time, c.end_time, c.capacity,
                   COALESCE((
                       SELECT COUNT(1)
                       FROM course_enrollment ce
                       WHERE ce.course_id = c.id AND ce.status = 'ENROLLED'
                   ), 0) AS enrolled_count,
                   c.price, c.description, c.status
            FROM course c
            LEFT JOIN employee e ON e.id = c.coach_id
            LEFT JOIN gym_room gr ON gr.id = c.gym_room_id
            WHERE c.id = #{id}
            LIMIT 1
            """)
    CourseVO findCourseDetail(@Param("id") Long id);

    @Insert("""
            INSERT INTO course (
                name, coach_id, gym_room_id, course_type, start_time, end_time,
                capacity, price, description, status
            ) VALUES (
                #{name}, #{coachId}, #{gymRoomId}, #{courseType}, #{startTime}, #{endTime},
                #{capacity}, #{price}, #{description}, #{status}
            )
            """)
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(Course course);

    @Update("""
            UPDATE course
            SET name = #{name},
                coach_id = #{coachId},
                gym_room_id = #{gymRoomId},
                course_type = #{courseType},
                start_time = #{startTime},
                end_time = #{endTime},
                capacity = #{capacity},
                price = #{price},
                description = #{description},
                status = #{status}
            WHERE id = #{id}
            """)
    int update(Course course);

    @Update("""
            UPDATE course
            SET status = #{status}
            WHERE id = #{id}
            """)
    int updateStatus(@Param("id") Long id, @Param("status") String status);
}
