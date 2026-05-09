package com.example.gym.employee.service;

import com.example.gym.admin.service.AdminGuard;
import com.example.gym.common.exception.BusinessException;
import com.example.gym.employee.dto.AdminEmployeeSaveDTO;
import com.example.gym.employee.entity.Employee;
import com.example.gym.employee.mapper.EmployeeMapper;
import com.example.gym.employee.vo.EmployeeVO;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class AdminEmployeeService {

    private final AdminGuard adminGuard;
    private final EmployeeMapper employeeMapper;

    public AdminEmployeeService(AdminGuard adminGuard, EmployeeMapper employeeMapper) {
        this.adminGuard = adminGuard;
        this.employeeMapper = employeeMapper;
    }

    public List<EmployeeVO> listEmployees() {
        adminGuard.requireAdmin();
        return employeeMapper.findAll();
    }

    public Employee getEmployeeDetail(Long employeeId) {
        adminGuard.requireAdmin();
        return requireExistingEmployee(employeeId);
    }

    @Transactional
    public Employee createEmployee(AdminEmployeeSaveDTO dto) {
        adminGuard.requireAdmin();
        Employee employee = new Employee();
        fillEmployee(employee, dto);
        employeeMapper.insert(employee);
        return getEmployeeDetail(employee.getId());
    }

    @Transactional
    public Employee updateEmployee(Long employeeId, AdminEmployeeSaveDTO dto) {
        adminGuard.requireAdmin();
        Employee employee = requireExistingEmployee(employeeId);
        fillEmployee(employee, dto);
        employeeMapper.update(employee);
        return getEmployeeDetail(employeeId);
    }

    @Transactional
    public void enableEmployee(Long employeeId) {
        adminGuard.requireAdmin();
        requireExistingEmployee(employeeId);
        employeeMapper.updateStatus(employeeId, "ACTIVE");
    }

    @Transactional
    public void disableEmployee(Long employeeId) {
        adminGuard.requireAdmin();
        requireExistingEmployee(employeeId);
        employeeMapper.updateStatus(employeeId, "DISABLED");
    }

    private Employee requireExistingEmployee(Long employeeId) {
        Employee employee = employeeMapper.findById(employeeId);
        if (employee == null) {
            throw new BusinessException("employee does not exist");
        }
        return employee;
    }

    private void fillEmployee(Employee employee, AdminEmployeeSaveDTO dto) {
        employee.setName(dto.getName());
        employee.setPhone(dto.getPhone());
        employee.setGender(dto.getGender());
        employee.setPosition(dto.getPosition());
        employee.setSpecialty(dto.getSpecialty());
        employee.setHireDate(dto.getHireDate());
        employee.setStatus(dto.getStatus());
    }
}
