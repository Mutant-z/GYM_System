package com.example.gym.employee.mapper;

import com.example.gym.employee.entity.Employee;
import com.example.gym.employee.vo.EmployeeVO;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.util.List;

@Mapper
public interface EmployeeMapper {

    @Select("""
            SELECT id, name, phone, gender, position, specialty, hire_date, status, created_at
            FROM employee
            ORDER BY id DESC
            """)
    List<EmployeeVO> findAll();

    @Select("""
            SELECT id, name, phone, gender, position, specialty, hire_date, status, created_at, updated_at
            FROM employee
            WHERE id = #{id}
            LIMIT 1
            """)
    Employee findById(@Param("id") Long id);

    @Insert("""
            INSERT INTO employee (name, phone, gender, position, specialty, hire_date, status)
            VALUES (#{name}, #{phone}, #{gender}, #{position}, #{specialty}, #{hireDate}, #{status})
            """)
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(Employee employee);

    @Update("""
            UPDATE employee
            SET name = #{name},
                phone = #{phone},
                gender = #{gender},
                position = #{position},
                specialty = #{specialty},
                hire_date = #{hireDate},
                status = #{status}
            WHERE id = #{id}
            """)
    int update(Employee employee);

    @Update("""
            UPDATE employee
            SET status = #{status}
            WHERE id = #{id}
            """)
    int updateStatus(@Param("id") Long id, @Param("status") String status);
}
