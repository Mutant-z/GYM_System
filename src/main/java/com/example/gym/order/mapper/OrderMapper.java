package com.example.gym.order.mapper;

import com.example.gym.order.entity.CommodityOrder;
import com.example.gym.order.entity.CommodityOrderItem;
import com.example.gym.order.vo.OrderItemVO;
import com.example.gym.order.vo.OrderVO;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;
import java.time.LocalDateTime;

@Mapper
public interface OrderMapper {

    @Insert("""
            INSERT INTO commodity_order (
                order_no, member_id, total_amount, pay_amount, status, payment_status,
                receiver_name, receiver_phone, receiver_address
            ) VALUES (
                #{orderNo}, #{memberId}, #{totalAmount}, #{payAmount}, #{status}, #{paymentStatus},
                #{receiverName}, #{receiverPhone}, #{receiverAddress}
            )
            """)
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insertOrder(CommodityOrder order);

    @Insert("""
            INSERT INTO commodity_order_item (
                order_id, commodity_id, commodity_name_snapshot, unit_price, quantity, subtotal_amount
            ) VALUES (
                #{orderId}, #{commodityId}, #{commodityNameSnapshot}, #{unitPrice}, #{quantity}, #{subtotalAmount}
            )
            """)
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insertOrderItem(CommodityOrderItem orderItem);

    @Select("""
            SELECT o.id, o.order_no, o.member_id, m.username AS member_username, m.nickname AS member_display_name,
                   o.total_amount, o.pay_amount, o.status, o.payment_status,
                   o.payment_time, o.receiver_name, o.receiver_phone, o.receiver_address, o.created_at
            FROM commodity_order o
            JOIN member m ON m.id = o.member_id
            WHERE o.member_id = #{memberId}
            ORDER BY o.created_at DESC, o.id DESC
            """)
    List<OrderVO> findByMemberId(@Param("memberId") Long memberId);

    @Select("""
            SELECT o.id, o.order_no, o.member_id, m.username AS member_username, m.nickname AS member_display_name,
                   o.total_amount, o.pay_amount, o.status, o.payment_status,
                   o.payment_time, o.receiver_name, o.receiver_phone, o.receiver_address, o.created_at
            FROM commodity_order o
            JOIN member m ON m.id = o.member_id
            ORDER BY o.created_at DESC, o.id DESC
            """)
    List<OrderVO> findAllOrders();

    @Select("""
            SELECT id
            FROM commodity_order
            WHERE payment_status = 'UNPAID'
              AND status = 'CREATED'
              AND created_at < #{cutoffTime}
            ORDER BY created_at ASC, id ASC
            """)
    List<Long> findExpiredUnpaidOrderIds(@Param("cutoffTime") LocalDateTime cutoffTime);

    @Select("""
            SELECT o.id, o.order_no, o.member_id, m.username AS member_username, m.nickname AS member_display_name,
                   o.total_amount, o.pay_amount, o.status, o.payment_status,
                   o.payment_time, o.receiver_name, o.receiver_phone, o.receiver_address, o.created_at, o.updated_at
            FROM commodity_order o
            JOIN member m ON m.id = o.member_id
            WHERE o.id = #{id}
            LIMIT 1
            """)
    CommodityOrder findById(@Param("id") Long id);

    @Select("""
            SELECT o.id, o.order_no, o.member_id, m.username AS member_username, m.nickname AS member_display_name,
                   o.total_amount, o.pay_amount, o.status, o.payment_status,
                   o.payment_time, o.receiver_name, o.receiver_phone, o.receiver_address, o.created_at
            FROM commodity_order o
            JOIN member m ON m.id = o.member_id
            WHERE o.id = #{id}
            LIMIT 1
            """)
    OrderVO findOrderVOById(@Param("id") Long id);

    @Select("""
            SELECT id, order_no, member_id, total_amount, pay_amount, status, payment_status,
                   payment_time, receiver_name, receiver_phone, receiver_address, created_at, updated_at
            FROM commodity_order
            WHERE id = #{id}
            LIMIT 1
            """)
    CommodityOrder findOrderEntityById(@Param("id") Long id);

    @Select("""
            SELECT 1
            FROM commodity_order
            WHERE id = #{id}
              AND payment_status = 'UNPAID'
              AND status = 'CREATED'
            LIMIT 1
            """)
    Integer existsUnpaidCreatedOrder(@Param("id") Long id);

    @org.apache.ibatis.annotations.Update("""
            UPDATE commodity_order
            SET status = #{status},
                payment_status = #{paymentStatus}
            WHERE id = #{id}
              AND payment_status = 'UNPAID'
              AND status = 'CREATED'
            """)
    int markOrderCanceledIfUnpaid(
            @Param("id") Long id,
            @Param("status") String status,
            @Param("paymentStatus") String paymentStatus
    );

    @Select("""
            SELECT id, commodity_id, commodity_name_snapshot, unit_price, quantity, subtotal_amount
            FROM commodity_order_item
            WHERE order_id = #{orderId}
            ORDER BY id ASC
            """)
    List<OrderItemVO> findItemsByOrderId(@Param("orderId") Long orderId);
}
