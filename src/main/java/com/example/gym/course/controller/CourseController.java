package com.example.gym.course.controller;

import com.example.gym.common.api.ApiResponse;
import com.example.gym.course.dto.AdminCourseCreateDTO;
import com.example.gym.course.dto.AdminCourseUpdateDTO;
import com.example.gym.course.dto.AdminEnrollmentQueryDTO;
import com.example.gym.course.dto.CourseQueryDTO;
import com.example.gym.course.dto.MyCourseQueryDTO;
import com.example.gym.course.service.CourseService;
import com.example.gym.course.vo.AdminCourseEnrollmentVO;
import com.example.gym.course.vo.CourseDetailVO;
import com.example.gym.course.vo.CourseVO;
import com.example.gym.course.vo.MyCourseVO;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/courses")
public class CourseController {

    private final CourseService courseService;

    public CourseController(CourseService courseService) {
        this.courseService = courseService;
    }

    @GetMapping
    public ApiResponse<List<CourseVO>> listCourses(@RequestParam(value = "status", required = false) String status) {
        CourseQueryDTO queryDTO = new CourseQueryDTO();
        queryDTO.setStatus(status);
        return ApiResponse.success(courseService.listCourses(queryDTO));
    }

    @GetMapping("/{id}")
    public ApiResponse<CourseDetailVO> getCourseDetail(@PathVariable Long id) {
        return ApiResponse.success(courseService.getCourseDetail(id));
    }

    @PostMapping("/{id}/enroll")
    public ApiResponse<MyCourseVO> enrollCourse(@PathVariable Long id) {
        return ApiResponse.success(courseService.enrollCourse(id));
    }

    @GetMapping("/me")
    public ApiResponse<List<MyCourseVO>> listMyCourses(@RequestParam(value = "status", required = false) String status) {
        MyCourseQueryDTO queryDTO = new MyCourseQueryDTO();
        queryDTO.setStatus(status);
        return ApiResponse.success(courseService.listMyCourses(queryDTO));
    }

    @PostMapping("/enrollments/{id}/cancel")
    public ApiResponse<Void> cancelEnrollment(@PathVariable Long id) {
        courseService.cancelEnrollment(id);
        return ApiResponse.success();
    }

    @PostMapping
    public ApiResponse<CourseDetailVO> adminCreateCourse(@Valid @RequestBody AdminCourseCreateDTO dto) {
        return ApiResponse.success(courseService.adminCreateCourse(dto));
    }

    @PutMapping("/{id}")
    public ApiResponse<CourseDetailVO> adminUpdateCourse(@PathVariable Long id, @Valid @RequestBody AdminCourseUpdateDTO dto) {
        return ApiResponse.success(courseService.adminUpdateCourse(id, dto));
    }

    @PostMapping("/{id}/disable")
    public ApiResponse<Void> adminDisableCourse(@PathVariable Long id) {
        courseService.adminDisableCourse(id);
        return ApiResponse.success();
    }

    @PostMapping("/{id}/enable")
    public ApiResponse<Void> adminEnableCourse(@PathVariable Long id) {
        courseService.adminEnableCourse(id);
        return ApiResponse.success();
    }

    @GetMapping("/enrollments")
    public ApiResponse<List<AdminCourseEnrollmentVO>> adminListEnrollments(
            @RequestParam(value = "enrollmentNo", required = false) String enrollmentNo,
            @RequestParam(value = "memberUsername", required = false) String memberUsername,
            @RequestParam(value = "courseId", required = false) Long courseId,
            @RequestParam(value = "status", required = false) String status
    ) {
        AdminEnrollmentQueryDTO queryDTO = new AdminEnrollmentQueryDTO();
        queryDTO.setEnrollmentNo(enrollmentNo);
        queryDTO.setMemberUsername(memberUsername);
        queryDTO.setCourseId(courseId);
        queryDTO.setStatus(status);
        return ApiResponse.success(courseService.adminListEnrollments(queryDTO));
    }

    @PostMapping("/enrollments/{id}/admin-cancel")
    public ApiResponse<Void> adminCancelEnrollment(@PathVariable Long id) {
        courseService.adminCancelEnrollment(id);
        return ApiResponse.success();
    }
}
