package com.example.gym.cart.mapper;

import com.example.gym.cart.entity.CartItem;
import com.example.gym.cart.vo.CartItemVO;
import org.apache.ibatis.annotations.Delete;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.util.List;

@Mapper
public interface CartItemMapper {

    @Select("""
            SELECT id, member_id, commodity_id, quantity, selected, created_at, updated_at
            FROM cart_item
            WHERE member_id = #{memberId} AND commodity_id = #{commodityId}
            LIMIT 1
            """)
    CartItem findByMemberIdAndCommodityId(@Param("memberId") Long memberId, @Param("commodityId") Long commodityId);

    @Insert("""
            INSERT INTO cart_item (member_id, commodity_id, quantity, selected)
            VALUES (#{memberId}, #{commodityId}, #{quantity}, #{selected})
            """)
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(CartItem cartItem);

    @Update("""
            UPDATE cart_item
            SET quantity = #{quantity},
                selected = #{selected}
            WHERE id = #{id}
            """)
    int update(CartItem cartItem);

    @Delete("""
            DELETE FROM cart_item
            WHERE id = #{id}
            """)
    int deleteById(@Param("id") Long id);

    @Select("""
            SELECT ci.id, ci.commodity_id, c.name AS commodity_name, c.category AS commodity_category,
                   c.price AS commodity_price, c.stock AS commodity_stock, c.cover_image,
                   ci.quantity, ci.selected, (c.price * ci.quantity) AS subtotal_amount, ci.created_at
            FROM cart_item ci
            JOIN commodity c ON c.id = ci.commodity_id
            WHERE ci.member_id = #{memberId}
            ORDER BY ci.created_at DESC, ci.id DESC
            """)
    List<CartItemVO> findByMemberId(@Param("memberId") Long memberId);

    @Select("""
            SELECT id, member_id, commodity_id, quantity, selected, created_at, updated_at
            FROM cart_item
            WHERE id = #{id}
            LIMIT 1
            """)
    CartItem findById(@Param("id") Long id);

    @Select({
            "<script>",
            "SELECT id, member_id, commodity_id, quantity, selected, created_at, updated_at",
            "FROM cart_item",
            "WHERE member_id = #{memberId}",
            "AND id IN",
            "<foreach collection='ids' item='id' open='(' separator=',' close=')'>",
            "#{id}",
            "</foreach>",
            "</script>"
    })
    List<CartItem> findByMemberIdAndIds(@Param("memberId") Long memberId, @Param("ids") List<Long> ids);
}
