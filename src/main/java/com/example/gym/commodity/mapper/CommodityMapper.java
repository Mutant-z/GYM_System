package com.example.gym.commodity.mapper;

import com.example.gym.commodity.entity.Commodity;
import com.example.gym.commodity.vo.CommodityVO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.util.List;

@Mapper
public interface CommodityMapper {

    @Select("""
            SELECT id, name, category, price, stock, cover_image, description, status
            FROM commodity
            WHERE status = 'ON_SALE'
            ORDER BY id DESC
            """)
    List<CommodityVO> findOnSaleCommodities();

    @Select("""
            SELECT id, name, category, price, stock, cover_image, description, status, created_at, updated_at
            FROM commodity
            WHERE id = #{id}
            LIMIT 1
            """)
    Commodity findById(@Param("id") Long id);

    @Select("""
            SELECT id, name, category, price, stock, cover_image, description, status
            FROM commodity
            WHERE id = #{id}
            LIMIT 1
            """)
    CommodityVO findCommodityDetail(@Param("id") Long id);

    @Select("""
            SELECT id, name, category, price, stock, cover_image, description, status
            FROM commodity
            ORDER BY id DESC
            """)
    List<CommodityVO> findAllCommodities();

    @Select("""
            SELECT id, name, category, price, stock, cover_image, description, status, created_at, updated_at
            FROM commodity
            WHERE name = #{name}
            LIMIT 1
            """)
    Commodity findByName(@Param("name") String name);

    @Insert("""
            INSERT INTO commodity (name, category, price, stock, cover_image, description, status)
            VALUES (#{name}, #{category}, #{price}, #{stock}, #{coverImage}, #{description}, #{status})
            """)
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(Commodity commodity);

    @Update("""
            UPDATE commodity
            SET name = #{name},
                category = #{category},
                price = #{price},
                stock = #{stock},
                cover_image = #{coverImage},
                description = #{description},
                status = #{status}
            WHERE id = #{id}
            """)
    int update(Commodity commodity);

    @Update("""
            UPDATE commodity
            SET status = #{status}
            WHERE id = #{id}
            """)
    int updateStatus(@Param("id") Long id, @Param("status") String status);

    @Update("""
            UPDATE commodity
            SET stock = #{stock}
            WHERE id = #{id}
            """)
    int updateStock(@Param("id") Long id, @Param("stock") Integer stock);

    @Update("""
            UPDATE commodity
            SET stock = stock - #{quantity}
            WHERE id = #{id}
              AND stock >= #{quantity}
            """)
    int decreaseStock(@Param("id") Long id, @Param("quantity") Integer quantity);

    @Update("""
            UPDATE commodity
            SET stock = stock + #{quantity}
            WHERE id = #{id}
            """)
    int increaseStock(@Param("id") Long id, @Param("quantity") Integer quantity);
}
