package com.example.gym.equipment.mapper;

import com.example.gym.equipment.entity.Equipment;
import com.example.gym.equipment.vo.EquipmentVO;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.util.List;

@Mapper
public interface EquipmentMapper {

    @Select("""
            SELECT e.id, e.gym_room_id, gr.name AS gym_room_name, e.name, e.category, e.brand, e.quantity,
                   e.status, e.purchase_date, e.description, e.created_at
            FROM equipment e
            LEFT JOIN gym_room gr ON gr.id = e.gym_room_id
            ORDER BY e.id DESC
            """)
    List<EquipmentVO> findAll();

    @Select("""
            SELECT id, gym_room_id, name, category, brand, quantity, status, purchase_date, description, created_at, updated_at
            FROM equipment
            WHERE id = #{id}
            LIMIT 1
            """)
    Equipment findById(@Param("id") Long id);

    @Insert("""
            INSERT INTO equipment (gym_room_id, name, category, brand, quantity, status, purchase_date, description)
            VALUES (#{gymRoomId}, #{name}, #{category}, #{brand}, #{quantity}, #{status}, #{purchaseDate}, #{description})
            """)
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(Equipment equipment);

    @Update("""
            UPDATE equipment
            SET gym_room_id = #{gymRoomId},
                name = #{name},
                category = #{category},
                brand = #{brand},
                quantity = #{quantity},
                status = #{status},
                purchase_date = #{purchaseDate},
                description = #{description}
            WHERE id = #{id}
            """)
    int update(Equipment equipment);

    @Update("""
            UPDATE equipment
            SET status = #{status}
            WHERE id = #{id}
            """)
    int updateStatus(@Param("id") Long id, @Param("status") String status);
}
