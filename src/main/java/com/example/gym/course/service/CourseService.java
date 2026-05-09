package com.example.gym.course.service;

import com.example.gym.auth.support.AuthConstants;
import com.example.gym.auth.support.AuthUser;
import com.example.gym.auth.support.UserContext;
import com.example.gym.common.api.ResultCode;
import com.example.gym.common.exception.BusinessException;
import com.example.gym.common.util.IdGenerator;
import com.example.gym.course.dto.CourseQueryDTO;
import com.example.gym.course.dto.MyCourseQueryDTO;
import com.example.gym.course.dto.AdminCourseCreateDTO;
import com.example.gym.course.dto.AdminCourseUpdateDTO;
import com.example.gym.course.dto.AdminEnrollmentQueryDTO;
import com.example.gym.course.entity.Course;
import com.example.gym.course.entity.CourseEnrollment;
import com.example.gym.course.mapper.CourseEnrollmentMapper;
import com.example.gym.course.mapper.CourseMapper;
import com.example.gym.course.vo.AdminCourseEnrollmentVO;
import com.example.gym.course.vo.CourseDetailVO;
import com.example.gym.course.vo.CourseVO;
import com.example.gym.course.vo.MyCourseVO;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class CourseService {

    private static final String COURSE_STATUS_OPEN = "OPEN";
    private static final String ENROLLMENT_STATUS_ENROLLED = "ENROLLED";
    private static final String ENROLLMENT_STATUS_CANCELED = "CANCELED";

    private final CourseMapper courseMapper;
    private final CourseEnrollmentMapper courseEnrollmentMapper;

    public CourseService(CourseMapper courseMapper, CourseEnrollmentMapper courseEnrollmentMapper) {
        this.courseMapper = courseMapper;
        this.courseEnrollmentMapper = courseEnrollmentMapper;
    }

    public List<CourseVO> listCourses(CourseQueryDTO queryDTO) {
        requireActiveMemberOrAdmin();
        String status = queryDTO == null ? null : queryDTO.getStatus();
        return courseMapper.findCourses(status);
    }

    public CourseDetailVO getCourseDetail(Long id) {
        requireActiveMemberOrAdmin();
        Course course = findExistingCourse(id);
        CourseVO detail = courseMapper.findCourseDetail(id);
        CourseDetailVO vo = new CourseDetailVO();
        vo.setId(detail.getId());
        vo.setName(detail.getName());
        vo.setCourseType(detail.getCourseType());
        vo.setCoachId(detail.getCoachId());
        vo.setCoachName(detail.getCoachName());
        vo.setGymRoomId(detail.getGymRoomId());
        vo.setGymRoomName(detail.getGymRoomName());
        vo.setStartTime(detail.getStartTime());
        vo.setEndTime(detail.getEndTime());
        vo.setCapacity(detail.getCapacity());
        vo.setEnrolledCount(detail.getEnrolledCount());
        vo.setPrice(detail.getPrice());
        vo.setDescription(detail.getDescription());
        vo.setStatus(detail.getStatus());
        vo.setEnrollable(COURSE_STATUS_OPEN.equalsIgnoreCase(course.getStatus()) && course.getStartTime().isAfter(LocalDateTime.now()));
        return vo;
    }

    @Transactional
    public MyCourseVO enrollCourse(Long courseId) {
        AuthUser currentUser = requireActiveMemberUser();
        Course course = findExistingCourse(courseId);
        validateCourseCanEnroll(course);
        validateCapacity(course);

        CourseEnrollment enrollment = courseEnrollmentMapper.findByMemberIdAndCourseId(currentUser.getUserId(), courseId);
        if (enrollment != null) {
            if (ENROLLMENT_STATUS_ENROLLED.equalsIgnoreCase(enrollment.getStatus())) {
                throw new BusinessException("you have already enrolled in this course");
            }
            courseEnrollmentMapper.updateStatus(enrollment.getId(), ENROLLMENT_STATUS_ENROLLED);
        } else {
            enrollment = new CourseEnrollment();
            enrollment.setEnrollmentNo(IdGenerator.businessId("en"));
            enrollment.setMemberId(currentUser.getUserId());
            enrollment.setCourseId(courseId);
            enrollment.setStatus(ENROLLMENT_STATUS_ENROLLED);
            courseEnrollmentMapper.insert(enrollment);
        }

        return courseEnrollmentMapper.findMyCourses(currentUser.getUserId(), ENROLLMENT_STATUS_ENROLLED).stream()
                .filter(item -> item.getCourseId().equals(courseId))
                .findFirst()
                .orElseThrow(() -> new BusinessException("failed to load enrollment result"));
    }

    public List<MyCourseVO> listMyCourses(MyCourseQueryDTO queryDTO) {
        AuthUser currentUser = requireActiveMemberUser();
        String status = queryDTO == null ? null : queryDTO.getStatus();
        return courseEnrollmentMapper.findMyCourses(currentUser.getUserId(), status);
    }

    @Transactional
    public CourseDetailVO adminCreateCourse(AdminCourseCreateDTO dto) {
        requireAdminUser();
        validateCourseTimeRange(dto.getStartTime(), dto.getEndTime());

        Course course = new Course();
        course.setName(dto.getName());
        course.setCoachId(dto.getCoachId());
        course.setGymRoomId(dto.getGymRoomId());
        course.setCourseType(dto.getCourseType());
        course.setStartTime(dto.getStartTime());
        course.setEndTime(dto.getEndTime());
        course.setCapacity(dto.getCapacity());
        course.setPrice(dto.getPrice());
        course.setDescription(dto.getDescription());
        course.setStatus(dto.getStatus());
        courseMapper.insert(course);
        return getCourseDetail(course.getId());
    }

    @Transactional
    public CourseDetailVO adminUpdateCourse(Long courseId, AdminCourseUpdateDTO dto) {
        requireAdminUser();
        Course course = findExistingCourse(courseId);
        validateCourseTimeRange(dto.getStartTime(), dto.getEndTime());

        course.setName(dto.getName());
        course.setCoachId(dto.getCoachId());
        course.setGymRoomId(dto.getGymRoomId());
        course.setCourseType(dto.getCourseType());
        course.setStartTime(dto.getStartTime());
        course.setEndTime(dto.getEndTime());
        course.setCapacity(dto.getCapacity());
        course.setPrice(dto.getPrice());
        course.setDescription(dto.getDescription());
        course.setStatus(dto.getStatus());
        courseMapper.update(course);
        return getCourseDetail(courseId);
    }

    @Transactional
    public void adminDisableCourse(Long courseId) {
        requireAdminUser();
        findExistingCourse(courseId);
        courseMapper.updateStatus(courseId, "CLOSED");
    }

    @Transactional
    public void adminEnableCourse(Long courseId) {
        requireAdminUser();
        findExistingCourse(courseId);
        courseMapper.updateStatus(courseId, COURSE_STATUS_OPEN);
    }

    public List<AdminCourseEnrollmentVO> adminListEnrollments(AdminEnrollmentQueryDTO queryDTO) {
        requireAdminUser();
        return courseEnrollmentMapper.findAllEnrollments(
                queryDTO == null ? null : queryDTO.getEnrollmentNo(),
                queryDTO == null ? null : queryDTO.getMemberUsername(),
                queryDTO == null ? null : queryDTO.getCourseId(),
                queryDTO == null ? null : queryDTO.getStatus()
        );
    }

    @Transactional
    public void cancelEnrollment(Long enrollmentId) {
        AuthUser currentUser = requireActiveMemberUser();
        CourseEnrollment enrollment = courseEnrollmentMapper.findById(enrollmentId);
        if (enrollment == null) {
            throw new BusinessException("course enrollment does not exist");
        }
        if (!enrollment.getMemberId().equals(currentUser.getUserId())) {
            throw new BusinessException(ResultCode.FORBIDDEN, "you can only cancel your own course enrollment");
        }
        if (!ENROLLMENT_STATUS_ENROLLED.equalsIgnoreCase(enrollment.getStatus())) {
            throw new BusinessException("current course enrollment cannot be canceled");
        }

        Course course = findExistingCourse(enrollment.getCourseId());
        if (!course.getStartTime().isAfter(LocalDateTime.now())) {
            throw new BusinessException("course that has started cannot be canceled");
        }

        courseEnrollmentMapper.updateStatus(enrollmentId, ENROLLMENT_STATUS_CANCELED);
    }

    @Transactional
    public void adminCancelEnrollment(Long enrollmentId) {
        requireAdminUser();
        CourseEnrollment enrollment = courseEnrollmentMapper.findById(enrollmentId);
        if (enrollment == null) {
            throw new BusinessException("course enrollment does not exist");
        }
        if (!ENROLLMENT_STATUS_ENROLLED.equalsIgnoreCase(enrollment.getStatus())) {
            throw new BusinessException("current course enrollment cannot be canceled");
        }
        Course course = findExistingCourse(enrollment.getCourseId());
        if (!course.getStartTime().isAfter(LocalDateTime.now())) {
            throw new BusinessException("course that has started cannot be canceled");
        }
        courseEnrollmentMapper.updateStatus(enrollmentId, ENROLLMENT_STATUS_CANCELED);
    }

    private Course findExistingCourse(Long courseId) {
        Course course = courseMapper.findById(courseId);
        if (course == null) {
            throw new BusinessException("course does not exist");
        }
        return course;
    }

    private void validateCourseCanEnroll(Course course) {
        if (!COURSE_STATUS_OPEN.equalsIgnoreCase(course.getStatus())) {
            throw new BusinessException("course is not open for enrollment");
        }
        if (!course.getStartTime().isAfter(LocalDateTime.now())) {
            throw new BusinessException("course has already started");
        }
    }

    private void validateCapacity(Course course) {
        int enrolledCount = courseEnrollmentMapper.countEnrolledByCourseId(course.getId());
        if (enrolledCount >= course.getCapacity()) {
            throw new BusinessException("course capacity is full");
        }
    }

    private void validateCourseTimeRange(LocalDateTime startTime, LocalDateTime endTime) {
        if (!startTime.isBefore(endTime)) {
            throw new BusinessException("course start time must be earlier than end time");
        }
    }

    private AuthUser requireMemberUser() {
        AuthUser authUser = UserContext.get();
        if (authUser == null) {
            throw new BusinessException(ResultCode.UNAUTHORIZED, "login required");
        }
        if (!AuthConstants.USER_TYPE_MEMBER.equals(authUser.getUserType())) {
            throw new BusinessException(ResultCode.FORBIDDEN, "member login required");
        }
        return authUser;
    }

    private AuthUser requireActiveMemberUser() {
        AuthUser authUser = requireMemberUser();
        if (!AuthConstants.isMemberActiveStatus(authUser.getStatus())) {
            throw new BusinessException(ResultCode.FORBIDDEN, "member account is not enabled");
        }
        return authUser;
    }

    private AuthUser requireActiveMemberOrAdmin() {
        AuthUser authUser = UserContext.get();
        if (authUser == null) {
            throw new BusinessException(ResultCode.UNAUTHORIZED, "login required");
        }
        if (AuthConstants.USER_TYPE_ADMIN.equals(authUser.getUserType())) {
            return authUser;
        }
        if (AuthConstants.USER_TYPE_MEMBER.equals(authUser.getUserType())
                && AuthConstants.isMemberActiveStatus(authUser.getStatus())) {
            return authUser;
        }
        throw new BusinessException(ResultCode.FORBIDDEN, "member account is not enabled");
    }

    private AuthUser requireAdminUser() {
        AuthUser authUser = UserContext.get();
        if (authUser == null) {
            throw new BusinessException(ResultCode.UNAUTHORIZED, "login required");
        }
        if (!AuthConstants.USER_TYPE_ADMIN.equals(authUser.getUserType())) {
            throw new BusinessException(ResultCode.FORBIDDEN, "admin login required");
        }
        return authUser;
    }
}
