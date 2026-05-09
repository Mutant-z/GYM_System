package com.example.gym.employee.controller;

import com.example.gym.common.api.ApiResponse;
import com.example.gym.employee.dto.AdminEmployeeSaveDTO;
import com.example.gym.employee.entity.Employee;
import com.example.gym.employee.service.AdminEmployeeService;
import com.example.gym.employee.vo.EmployeeVO;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/admin/employees")
public class AdminEmployeeController {

    private final AdminEmployeeService adminEmployeeService;

    public AdminEmployeeController(AdminEmployeeService adminEmployeeService) {
        this.adminEmployeeService = adminEmployeeService;
    }

    @GetMapping
    public ApiResponse<List<EmployeeVO>> listEmployees() {
        return ApiResponse.success(adminEmployeeService.listEmployees());
    }

    @GetMapping("/{id}")
    public ApiResponse<Employee> getEmployeeDetail(@PathVariable("id") Long id) {
        return ApiResponse.success(adminEmployeeService.getEmployeeDetail(id));
    }

    @PostMapping
    public ApiResponse<Employee> createEmployee(@Valid @RequestBody AdminEmployeeSaveDTO dto) {
        return ApiResponse.success(adminEmployeeService.createEmployee(dto));
    }

    @PutMapping("/{id}")
    public ApiResponse<Employee> updateEmployee(@PathVariable("id") Long id, @Valid @RequestBody AdminEmployeeSaveDTO dto) {
        return ApiResponse.success(adminEmployeeService.updateEmployee(id, dto));
    }

    @PostMapping("/{id}/enable")
    public ApiResponse<Void> enableEmployee(@PathVariable("id") Long id) {
        adminEmployeeService.enableEmployee(id);
        return ApiResponse.success();
    }

    @PostMapping("/{id}/disable")
    public ApiResponse<Void> disableEmployee(@PathVariable("id") Long id) {
        adminEmployeeService.disableEmployee(id);
        return ApiResponse.success();
    }
}
