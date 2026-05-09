package com.example.gym.cart.controller;

import com.example.gym.cart.dto.AddCartItemDTO;
import com.example.gym.cart.dto.UpdateCartItemDTO;
import com.example.gym.cart.service.CartService;
import com.example.gym.cart.vo.CartItemVO;
import com.example.gym.common.api.ApiResponse;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/cart/items")
public class CartController {

    private final CartService cartService;

    public CartController(CartService cartService) {
        this.cartService = cartService;
    }

    @PostMapping
    public ApiResponse<CartItemVO> addCartItem(@Valid @RequestBody AddCartItemDTO dto) {
        return ApiResponse.success(cartService.addCartItem(dto));
    }

    @GetMapping
    public ApiResponse<List<CartItemVO>> listMyCartItems() {
        return ApiResponse.success(cartService.listMyCartItems());
    }

    @PutMapping("/{id}")
    public ApiResponse<CartItemVO> updateCartItem(@PathVariable Long id, @Valid @RequestBody UpdateCartItemDTO dto) {
        return ApiResponse.success(cartService.updateCartItem(id, dto));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> deleteCartItem(@PathVariable Long id) {
        cartService.deleteCartItem(id);
        return ApiResponse.success();
    }
}
