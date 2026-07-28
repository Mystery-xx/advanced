package com.example.orderservice.controller;

import com.example.orderservice.dto.CreateOrderRequest;
import com.example.orderservice.dto.UpdateStatusRequest;
import com.example.orderservice.entity.Order;
import com.example.orderservice.repository.OrderRepository;
import com.example.orderservice.repository.OrderStatusHistoryRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;

import static org.hamcrest.Matchers.*;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@Transactional
class OrderControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private OrderRepository orderRepository;

    @Autowired
    private OrderStatusHistoryRepository orderStatusHistoryRepository;

    @BeforeEach
    void setUp() {
        orderRepository.deleteAll();
        orderStatusHistoryRepository.deleteAll();
    }

    @Test
    @DisplayName("GET /api/orders - should return empty list when no orders exist")
    @WithMockUser(roles = "ADMIN")
    void getAllOrders_emptyList() throws Exception {
        mockMvc.perform(get("/api/orders"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.content", is(empty())))
            .andExpect(jsonPath("$.totalElements", is(0)))
            .andExpect(jsonPath("$.totalPages", is(0)))
            .andExpect(jsonPath("$.number", is(0)))
            .andExpect(jsonPath("$.size", is(20)));
    }

    @Test
    @DisplayName("GET /api/orders - should return populated list of orders")
    @WithMockUser(roles = "ADMIN")
    void getAllOrders_populatedList() throws Exception {
        createOrder("user123", new BigDecimal("150.00"), "PENDING");
        createOrder("user456", new BigDecimal("250.00"), "CONFIRMED");

        mockMvc.perform(get("/api/orders"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.content", hasSize(2)))
            .andExpect(jsonPath("$.totalElements", is(2)))
            .andExpect(jsonPath("$.content[0].userId", is("user123")))
            .andExpect(jsonPath("$.content[0].totalAmount", is(150.0)))
            .andExpect(jsonPath("$.content[1].userId", is("user456")))
            .andExpect(jsonPath("$.content[1].totalAmount", is(250.0)));
    }

    @Test
    @DisplayName("GET /api/orders/{id} - should return order when found")
    @WithMockUser(roles = "USER")
    void getOrderById_found() throws Exception {
        Order order = createOrder("user123", new BigDecimal("100.00"), "PENDING");

        mockMvc.perform(get("/api/orders/{id}", order.getId()))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id", is(order.getId().intValue())))
            .andExpect(jsonPath("$.userId", is("user123")))
            .andExpect(jsonPath("$.totalAmount", is(100.0)))
            .andExpect(jsonPath("$.status", is("PENDING")))
            .andExpect(jsonPath("$.shippingAddress", is("123 Test St")))
            .andExpect(jsonPath("$.items", is("item1,item2")));
    }

    @Test
    @DisplayName("GET /api/orders/{id} - should return 404 when order not found")
    @WithMockUser(roles = "USER")
    void getOrderById_notFound() throws Exception {
        mockMvc.perform(get("/api/orders/{id}", 999L))
            .andExpect(status().isNotFound());
    }

    @Test
    @DisplayName("POST /api/orders - should create order successfully")
    @WithMockUser(roles = "USER")
    void createOrder_success() throws Exception {
        CreateOrderRequest request = new CreateOrderRequest();
        request.setUserId("user789");
        request.setTotalAmount(new BigDecimal("299.99"));
        request.setShippingAddress("456 Main St");
        request.setItems("laptop,mouse");

        mockMvc.perform(post("/api/orders")
                .with(csrf())
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.userId", is("user789")))
            .andExpect(jsonPath("$.totalAmount", is(299.99)))
            .andExpect(jsonPath("$.status", is("PENDING")))
            .andExpect(jsonPath("$.shippingAddress", is("456 Main St")))
            .andExpect(jsonPath("$.items", is("laptop,mouse")))
            .andExpect(jsonPath("$.id", notNullValue()));
    }

    @Test
    @DisplayName("POST /api/orders - should return 400 when userId is blank")
    @WithMockUser(roles = "USER")
    void createOrder_validationError_blankUserId() throws Exception {
        CreateOrderRequest request = new CreateOrderRequest();
        request.setUserId("");
        request.setTotalAmount(new BigDecimal("100.00"));

        mockMvc.perform(post("/api/orders")
                .with(csrf())
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("POST /api/orders - should return 400 when totalAmount is missing")
    @WithMockUser(roles = "USER")
    void createOrder_validationError_missingTotalAmount() throws Exception {
        CreateOrderRequest request = new CreateOrderRequest();
        request.setUserId("user123");

        mockMvc.perform(post("/api/orders")
                .with(csrf())
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("POST /api/orders - should return 400 when totalAmount is zero")
    @WithMockUser(roles = "USER")
    void createOrder_validationError_zeroTotalAmount() throws Exception {
        CreateOrderRequest request = new CreateOrderRequest();
        request.setUserId("user123");
        request.setTotalAmount(BigDecimal.ZERO);

        mockMvc.perform(post("/api/orders")
                .with(csrf())
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("PUT /api/orders/{id}/status - should update order status successfully")
    @WithMockUser(roles = "ADMIN")
    void updateOrderStatus_success() throws Exception {
        Order order = createOrder("user123", new BigDecimal("100.00"), "PENDING");

        UpdateStatusRequest request = new UpdateStatusRequest();
        request.setStatus("CONFIRMED");

        mockMvc.perform(put("/api/orders/{id}/status", order.getId())
                .with(csrf())
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id", is(order.getId().intValue())))
            .andExpect(jsonPath("$.status", is("CONFIRMED")));
    }

    @Test
    @DisplayName("PUT /api/orders/{id}/status - should return 400 when status is invalid")
    @WithMockUser(roles = "ADMIN")
    void updateOrderStatus_invalidStatus() throws Exception {
        Order order = createOrder("user123", new BigDecimal("100.00"), "PENDING");

        UpdateStatusRequest request = new UpdateStatusRequest();
        request.setStatus("INVALID_STATUS");

        mockMvc.perform(put("/api/orders/{id}/status", order.getId())
                .with(csrf())
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("PUT /api/orders/{id}/status - should return 400 when order not found")
    @WithMockUser(roles = "ADMIN")
    void updateOrderStatus_notFound() throws Exception {
        UpdateStatusRequest request = new UpdateStatusRequest();
        request.setStatus("CONFIRMED");

        mockMvc.perform(put("/api/orders/{id}/status", 999L)
                .with(csrf())
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("PUT /api/orders/{id}/status - should return 400 when status is blank")
    @WithMockUser(roles = "ADMIN")
    void updateOrderStatus_validationError_blankStatus() throws Exception {
        Order order = createOrder("user123", new BigDecimal("100.00"), "PENDING");

        UpdateStatusRequest request = new UpdateStatusRequest();
        request.setStatus("");

        mockMvc.perform(put("/api/orders/{id}/status", order.getId())
                .with(csrf())
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("POST /api/orders/{id}/cancel - should cancel order successfully (alternative to DELETE)")
    @WithMockUser(roles = "USER")
    void cancelOrder_asDelete_success() throws Exception {
        Order order = createOrder("user123", new BigDecimal("100.00"), "PENDING");

        mockMvc.perform(post("/api/orders/{id}/cancel", order.getId())
                .with(csrf()))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.status", is("CANCELLED")));
    }

    @Test
    @DisplayName("GET /api/orders - should return 403 when user has no ADMIN role")
    @WithMockUser(roles = "USER")
    void getAllOrders_forbidden() throws Exception {
        mockMvc.perform(get("/api/orders"))
            .andExpect(status().isForbidden());
    }

    @Test
    @DisplayName("GET /api/orders/user/{userId} - should return orders for specific user")
    @WithMockUser(roles = "USER")
    void getOrdersByUserId_success() throws Exception {
        createOrder("user123", new BigDecimal("100.00"), "PENDING");
        createOrder("user123", new BigDecimal("200.00"), "CONFIRMED");
        createOrder("user456", new BigDecimal("300.00"), "PENDING");

        mockMvc.perform(get("/api/orders/user/{userId}", "user123"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.content", hasSize(2)))
            .andExpect(jsonPath("$.totalElements", is(2)))
            .andExpect(jsonPath("$.content[*].userId", everyItem(is("user123"))));
    }

    @Test
    @DisplayName("GET /api/orders/status/{status} - should return orders filtered by status")
    @WithMockUser(roles = "ADMIN")
    void getOrdersByStatus_success() throws Exception {
        createOrder("user123", new BigDecimal("100.00"), "PENDING");
        createOrder("user456", new BigDecimal("200.00"), "PENDING");
        createOrder("user789", new BigDecimal("300.00"), "CONFIRMED");

        mockMvc.perform(get("/api/orders/status/{status}", "PENDING"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.content", hasSize(2)))
            .andExpect(jsonPath("$.content[*].status", everyItem(is("PENDING"))));
    }

    @Test
    @DisplayName("GET /api/orders/status/{status} - should return 400 for invalid status")
    @WithMockUser(roles = "ADMIN")
    void getOrdersByStatus_invalidStatus() throws Exception {
        mockMvc.perform(get("/api/orders/status/{status}", "INVALID_STATUS"))
            .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("GET /api/orders/{id}/history - should return 200 OK for order history endpoint")
    @WithMockUser(roles = "USER")
    void getOrderHistory_endpointExists() throws Exception {
        Order order = createOrder("user123", new BigDecimal("100.00"), "PENDING");

        mockMvc.perform(get("/api/orders/{id}/history", order.getId()))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.content").exists())
            .andExpect(jsonPath("$.totalElements").exists());
    }

    @Test
    @DisplayName("POST /api/orders/{id}/cancel - should cancel order successfully")
    @WithMockUser(roles = "USER")
    void cancelOrder_success() throws Exception {
        Order order = createOrder("user123", new BigDecimal("100.00"), "PENDING");

        mockMvc.perform(post("/api/orders/{id}/cancel", order.getId())
                .with(csrf()))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.status", is("CANCELLED")));
    }

    @Test
    @DisplayName("POST /api/orders/{id}/cancel - should return 400 when cancelling cancelled order")
    @WithMockUser(roles = "USER")
    void cancelOrder_alreadyCancelled() throws Exception {
        Order order = createOrder("user123", new BigDecimal("100.00"), "CANCELLED");

        mockMvc.perform(post("/api/orders/{id}/cancel", order.getId())
                .with(csrf()))
            .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("POST /api/orders/{id}/cancel - should return 400 when cancelling shipped order")
    @WithMockUser(roles = "USER")
    void cancelOrder_shippedOrder() throws Exception {
        Order order = createOrder("user123", new BigDecimal("100.00"), "SHIPPED");

        mockMvc.perform(post("/api/orders/{id}/cancel", order.getId())
                .with(csrf()))
            .andExpect(status().isBadRequest());
    }

    private Order createOrder(String userId, BigDecimal totalAmount, String status) {
        Order order = Order.builder()
            .userId(userId)
            .totalAmount(totalAmount)
            .status(Order.OrderStatus.valueOf(status))
            .shippingAddress("123 Test St")
            .items("item1,item2")
            .build();
        return orderRepository.save(order);
    }
}