// 文件作用：Go 后端的核心会员/商品/购物车/订单业务接口。
// 这里主要复现 Spring Boot 后端中和会员资料、管理员会员管理、
// 商品管理、购物车下单、订单查询/取消相关的接口。
// 这些接口直接操作 gym_system 数据库，并通过 main.go 中的统一响应格式返回给前端。
package main

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"time"
)

// getMyProfile 返回当前登录会员自己的资料。
func (app *App) getMyProfile(w http.ResponseWriter, r *http.Request) error {
	user := currentAuthUser(r)
	row, err := app.getMemberProfile(r, user.UserID)
	if err != nil {
		return err
	}
	return writeSuccess(w, row)
}

// getMemberProfile 查询会员资料详情。
// 它被会员端“我的资料”和管理员端“会员详情”复用，统一过滤 deleted=0 的软删除数据。
func (app *App) getMemberProfile(r *http.Request, memberID int64) (map[string]any, error) {
	rows, err := app.queryMaps(
		r.Context(),
		`SELECT id, username, nickname, real_name AS realName, gender, phone, email,
		        DATE_FORMAT(birthday, '%Y-%m-%d') AS birthday,
		        height_cm AS heightCm, weight_kg AS weightKg, fitness_goal AS fitnessGoal,
		        preferred_training_time AS preferredTrainingTime, injury_notes AS injuryNotes,
		        membership_status AS membershipStatus, last_login_at AS lastLoginAt,
		        created_at AS createdAt, updated_at AS updatedAt
		 FROM member WHERE id = ? AND deleted = 0 LIMIT 1`,
		memberID,
	)
	if err != nil {
		return nil, err
	}
	row, ok := firstRow(rows)
	if !ok {
		return nil, notFound("member does not exist")
	}
	return row, nil
}

// updateMyProfile 更新当前会员自己的资料。
// 账号、密码、会员状态等敏感字段不在这里修改，避免会员越权改变登录身份。
func (app *App) updateMyProfile(w http.ResponseWriter, r *http.Request) error {
	user := currentAuthUser(r)
	body, err := decodeJSON(r)
	if err != nil {
		return err
	}
	birthday, err := parseDate(asString(body["birthday"]))
	if err != nil {
		return badRequest("birthday is invalid")
	}
	_, err = app.db.ExecContext(
		r.Context(),
		`UPDATE member
		 SET nickname = ?, real_name = ?, gender = ?, phone = ?, email = ?, birthday = ?,
		     height_cm = ?, weight_kg = ?, fitness_goal = ?, preferred_training_time = ?, injury_notes = ?
		 WHERE id = ? AND deleted = 0`,
		asString(body["nickname"]),
		nullableString(body, "realName"),
		nullableString(body, "gender"),
		asString(body["phone"]),
		nullableString(body, "email"),
		birthday,
		nullableString(body, "heightCm"),
		nullableString(body, "weightKg"),
		nullableString(body, "fitnessGoal"),
		nullableString(body, "preferredTrainingTime"),
		nullableString(body, "injuryNotes"),
		user.UserID,
	)
	if err != nil {
		return err
	}
	return app.getMyProfile(w, r)
}

// adminListMembers 管理员查询会员列表。
// 支持按 username/nickname/phone/membershipStatus 过滤，返回字段对齐前端表格。
func (app *App) adminListMembers(w http.ResponseWriter, r *http.Request) error {
	q := r.URL.Query()
	query := `SELECT id, username, nickname, real_name AS realName, gender, phone, email,
	                 DATE_FORMAT(birthday, '%Y-%m-%d') AS birthday,
	                 height_cm AS heightCm, weight_kg AS weightKg, fitness_goal AS fitnessGoal,
	                 preferred_training_time AS preferredTrainingTime, injury_notes AS injuryNotes,
	                 membership_status AS membershipStatus, last_login_at AS lastLoginAt,
	                 created_at AS createdAt, updated_at AS updatedAt
	          FROM member WHERE deleted = 0`
	args := []any{}
	if v := strings.TrimSpace(q.Get("username")); v != "" {
		query += " AND username LIKE ?"
		args = append(args, "%"+v+"%")
	}
	if v := strings.TrimSpace(q.Get("nickname")); v != "" {
		query += " AND nickname LIKE ?"
		args = append(args, "%"+v+"%")
	}
	if v := strings.TrimSpace(q.Get("phone")); v != "" {
		query += " AND phone LIKE ?"
		args = append(args, "%"+v+"%")
	}
	if v := strings.TrimSpace(q.Get("membershipStatus")); v != "" {
		query += " AND membership_status = ?"
		args = append(args, v)
	}
	query += " ORDER BY created_at DESC, id DESC"
	rows, err := app.queryMaps(r.Context(), query, args...)
	if err != nil {
		return err
	}
	return writeSuccess(w, rows)
}

// adminGetMember 查询单个会员，并额外统计预约数、已报名课程数和订单数。
func (app *App) adminGetMember(w http.ResponseWriter, r *http.Request) error {
	id, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	profile, err := app.getMemberProfile(r, id)
	if err != nil {
		return err
	}
	var bookingCount, enrolledCourseCount, orderCount int64
	_ = app.db.QueryRowContext(r.Context(), `SELECT COUNT(1) FROM gym_booking WHERE member_id = ?`, id).Scan(&bookingCount)
	_ = app.db.QueryRowContext(r.Context(), `SELECT COUNT(1) FROM course_enrollment WHERE member_id = ? AND status = 'ENROLLED'`, id).Scan(&enrolledCourseCount)
	_ = app.db.QueryRowContext(r.Context(), `SELECT COUNT(1) FROM commodity_order WHERE member_id = ?`, id).Scan(&orderCount)
	profile["bookingCount"] = bookingCount
	profile["enrolledCourseCount"] = enrolledCourseCount
	profile["orderCount"] = orderCount
	return writeSuccess(w, profile)
}

// adminUpdateMember 管理员编辑会员资料。
// 这里和会员自助编辑使用相近字段，但由管理员权限入口调用。
func (app *App) adminUpdateMember(w http.ResponseWriter, r *http.Request) error {
	id, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	body, err := decodeJSON(r)
	if err != nil {
		return err
	}
	birthday, err := parseDate(asString(body["birthday"]))
	if err != nil {
		return badRequest("birthday is invalid")
	}
	_, err = app.db.ExecContext(
		r.Context(),
		`UPDATE member
		 SET nickname = ?, real_name = ?, gender = ?, phone = ?, email = ?, birthday = ?,
		     height_cm = ?, weight_kg = ?, fitness_goal = ?, preferred_training_time = ?, injury_notes = ?
		 WHERE id = ? AND deleted = 0`,
		asString(body["nickname"]),
		nullableString(body, "realName"),
		nullableString(body, "gender"),
		asString(body["phone"]),
		nullableString(body, "email"),
		birthday,
		nullableString(body, "heightCm"),
		nullableString(body, "weightKg"),
		nullableString(body, "fitnessGoal"),
		nullableString(body, "preferredTrainingTime"),
		nullableString(body, "injuryNotes"),
		id,
	)
	if err != nil {
		return err
	}
	return app.adminGetMember(w, r)
}

func (app *App) adminEnableMember(w http.ResponseWriter, r *http.Request) error {
	return app.updateMemberStatus(w, r, "ACTIVE")
}

func (app *App) adminDisableMember(w http.ResponseWriter, r *http.Request) error {
	return app.updateMemberStatus(w, r, "DISABLED")
}

// updateMemberStatus 启用/禁用会员账号。
// ACTIVE 会员可以预约和报名，DISABLED 会员会被登录/业务权限拦截。
func (app *App) updateMemberStatus(w http.ResponseWriter, r *http.Request, status string) error {
	id, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	_, err = app.db.ExecContext(r.Context(), `UPDATE member SET membership_status = ? WHERE id = ? AND deleted = 0`, status, id)
	if err != nil {
		return err
	}
	return writeSuccess(w, nil)
}

// listCommodities 返回会员端可购买商品，只展示 ON_SALE 商品。
func (app *App) listCommodities(w http.ResponseWriter, r *http.Request) error {
	rows, err := app.queryMaps(
		r.Context(),
		`SELECT id, name, category, price, stock, cover_image AS coverImage, description, status
		 FROM commodity WHERE status = 'ON_SALE' ORDER BY id DESC`,
	)
	if err != nil {
		return err
	}
	return writeSuccess(w, rows)
}

func (app *App) getCommodity(w http.ResponseWriter, r *http.Request) error {
	id, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	row, err := app.commodityDetail(r, id)
	if err != nil {
		return err
	}
	return writeSuccess(w, row)
}

// commodityDetail 查询商品详情，并计算 purchasable 字段供前端控制购买按钮。
func (app *App) commodityDetail(r *http.Request, id int64) (map[string]any, error) {
	rows, err := app.queryMaps(
		r.Context(),
		`SELECT id, name, category, price, stock, cover_image AS coverImage, description, status,
		        created_at AS createdAt, updated_at AS updatedAt
		 FROM commodity WHERE id = ? LIMIT 1`,
		id,
	)
	if err != nil {
		return nil, err
	}
	row, ok := firstRow(rows)
	if !ok {
		return nil, notFound("commodity does not exist")
	}
	row["purchasable"] = strings.EqualFold(asString(row["status"]), "ON_SALE") && toInt(row["stock"]) > 0
	return row, nil
}

// adminListCommodities 管理员查看所有商品，包括下架商品。
func (app *App) adminListCommodities(w http.ResponseWriter, r *http.Request) error {
	rows, err := app.queryMaps(
		r.Context(),
		`SELECT id, name, category, price, stock, cover_image AS coverImage, description, status
		 FROM commodity ORDER BY id DESC`,
	)
	if err != nil {
		return err
	}
	return writeSuccess(w, rows)
}

func (app *App) adminGetCommodity(w http.ResponseWriter, r *http.Request) error {
	return app.getCommodity(w, r)
}

// adminCreateCommodity 新增商品。
// price/coverImage/description 等字段允许为空，以兼容前端的轻量录入。
func (app *App) adminCreateCommodity(w http.ResponseWriter, r *http.Request) error {
	body, err := decodeJSON(r)
	if err != nil {
		return err
	}
	name, err := requiredString(body, "name")
	if err != nil {
		return err
	}
	res, err := app.db.ExecContext(
		r.Context(),
		`INSERT INTO commodity (name, category, price, stock, cover_image, description, status)
		 VALUES (?, ?, ?, ?, ?, ?, ?)`,
		name,
		nullableString(body, "category"),
		nullableString(body, "price"),
		asInt(body, "stock", 0),
		nullableString(body, "coverImage"),
		nullableString(body, "description"),
		defaultString(asString(body["status"]), "ON_SALE"),
	)
	if err != nil {
		return err
	}
	id, _ := res.LastInsertId()
	row, err := app.commodityDetail(r, id)
	if err != nil {
		return err
	}
	return writeSuccess(w, row)
}

// adminUpdateCommodity 更新商品基础信息、库存和上下架状态。
func (app *App) adminUpdateCommodity(w http.ResponseWriter, r *http.Request) error {
	id, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	body, err := decodeJSON(r)
	if err != nil {
		return err
	}
	_, err = app.db.ExecContext(
		r.Context(),
		`UPDATE commodity SET name = ?, category = ?, price = ?, stock = ?, cover_image = ?, description = ?, status = ? WHERE id = ?`,
		asString(body["name"]),
		nullableString(body, "category"),
		nullableString(body, "price"),
		asInt(body, "stock", 0),
		nullableString(body, "coverImage"),
		nullableString(body, "description"),
		defaultString(asString(body["status"]), "ON_SALE"),
		id,
	)
	if err != nil {
		return err
	}
	row, err := app.commodityDetail(r, id)
	if err != nil {
		return err
	}
	return writeSuccess(w, row)
}

func (app *App) adminCommodityOnSale(w http.ResponseWriter, r *http.Request) error {
	return app.updateCommodityStatus(w, r, "ON_SALE")
}

func (app *App) adminCommodityOffSale(w http.ResponseWriter, r *http.Request) error {
	return app.updateCommodityStatus(w, r, "OFF_SALE")
}

// updateCommodityStatus 切换商品 ON_SALE/OFF_SALE。
func (app *App) updateCommodityStatus(w http.ResponseWriter, r *http.Request, status string) error {
	id, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	_, err = app.db.ExecContext(r.Context(), `UPDATE commodity SET status = ? WHERE id = ?`, status, id)
	if err != nil {
		return err
	}
	return writeSuccess(w, nil)
}

// adminCommodityStock 单独调整商品库存。
func (app *App) adminCommodityStock(w http.ResponseWriter, r *http.Request) error {
	id, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	body, err := decodeJSON(r)
	if err != nil {
		return err
	}
	_, err = app.db.ExecContext(r.Context(), `UPDATE commodity SET stock = ? WHERE id = ?`, asInt(body, "stock", 0), id)
	if err != nil {
		return err
	}
	return writeSuccess(w, nil)
}

// addCartItem 把商品加入购物车。
// 如果同一会员已存在相同商品，则累加数量；同时校验商品是否上架和库存是否足够。
func (app *App) addCartItem(w http.ResponseWriter, r *http.Request) error {
	user := currentAuthUser(r)
	body, err := decodeJSON(r)
	if err != nil {
		return err
	}
	commodityID := int64(asInt(body, "commodityId", 0))
	quantity := asInt(body, "quantity", 1)
	if commodityID <= 0 || quantity <= 0 {
		return badRequest("commodityId and quantity are required")
	}
	var stock int
	var status string
	err = app.db.QueryRowContext(r.Context(), `SELECT stock, status FROM commodity WHERE id = ?`, commodityID).Scan(&stock, &status)
	if errors.Is(err, sql.ErrNoRows) {
		return notFound("commodity does not exist")
	}
	if err != nil {
		return err
	}
	if !strings.EqualFold(status, "ON_SALE") {
		return badRequest("commodity is not available for sale")
	}

	var existingID int64
	var existingQty int
	err = app.db.QueryRowContext(
		r.Context(),
		`SELECT id, quantity FROM cart_item WHERE member_id = ? AND commodity_id = ? LIMIT 1`,
		user.UserID,
		commodityID,
	).Scan(&existingID, &existingQty)
	if err == nil {
		if existingQty+quantity > stock {
			return badRequest("commodity stock is insufficient")
		}
		_, err = app.db.ExecContext(r.Context(), `UPDATE cart_item SET quantity = ?, selected = 1 WHERE id = ?`, existingQty+quantity, existingID)
		if err != nil {
			return err
		}
	} else if errors.Is(err, sql.ErrNoRows) {
		if quantity > stock {
			return badRequest("commodity stock is insufficient")
		}
		res, err := app.db.ExecContext(
			r.Context(),
			`INSERT INTO cart_item (member_id, commodity_id, quantity, selected) VALUES (?, ?, ?, 1)`,
			user.UserID,
			commodityID,
			quantity,
		)
		if err != nil {
			return err
		}
		existingID, _ = res.LastInsertId()
	} else {
		return err
	}

	item, err := app.cartItemByID(r, user.UserID, existingID)
	if err != nil {
		return err
	}
	return writeSuccess(w, item)
}

// listCartItems 返回当前会员购物车列表。
func (app *App) listCartItems(w http.ResponseWriter, r *http.Request) error {
	user := currentAuthUser(r)
	rows, err := app.cartItems(r, user.UserID)
	if err != nil {
		return err
	}
	return writeSuccess(w, rows)
}

// updateCartItem 修改购物车商品数量和勾选状态。
// 这里会重新读取当前库存，避免前端拿旧库存提交导致超卖。
func (app *App) updateCartItem(w http.ResponseWriter, r *http.Request) error {
	user := currentAuthUser(r)
	id, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	body, err := decodeJSON(r)
	if err != nil {
		return err
	}
	quantity := asInt(body, "quantity", 1)
	selected := 0
	if asBool(body["selected"], true) {
		selected = 1
	}
	var commodityID int64
	var stock int
	err = app.db.QueryRowContext(
		r.Context(),
		`SELECT ci.commodity_id, c.stock
		 FROM cart_item ci JOIN commodity c ON c.id = ci.commodity_id
		 WHERE ci.id = ? AND ci.member_id = ?`,
		id,
		user.UserID,
	).Scan(&commodityID, &stock)
	if errors.Is(err, sql.ErrNoRows) {
		return notFound("cart item does not exist")
	}
	if err != nil {
		return err
	}
	if quantity <= 0 || quantity > stock {
		return badRequest("commodity stock is insufficient")
	}
	_, err = app.db.ExecContext(r.Context(), `UPDATE cart_item SET quantity = ?, selected = ? WHERE id = ?`, quantity, selected, id)
	if err != nil {
		return err
	}
	item, err := app.cartItemByID(r, user.UserID, id)
	if err != nil {
		return err
	}
	return writeSuccess(w, item)
}

// deleteCartItem 删除当前会员自己的购物车条目。
func (app *App) deleteCartItem(w http.ResponseWriter, r *http.Request) error {
	user := currentAuthUser(r)
	id, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	res, err := app.db.ExecContext(r.Context(), `DELETE FROM cart_item WHERE id = ? AND member_id = ?`, id, user.UserID)
	if err != nil {
		return err
	}
	affected, _ := res.RowsAffected()
	if affected == 0 {
		return notFound("cart item does not exist")
	}
	return writeSuccess(w, nil)
}

// cartItems 查询购物车列表，并计算每行 subtotalAmount。
func (app *App) cartItems(r *http.Request, memberID int64) ([]map[string]any, error) {
	return app.queryMaps(
		r.Context(),
		`SELECT ci.id, ci.commodity_id AS commodityId, c.name AS commodityName,
		        c.category AS commodityCategory, c.price AS commodityPrice, c.stock AS commodityStock,
		        c.cover_image AS coverImage, ci.quantity, ci.selected,
		        (c.price * ci.quantity) AS subtotalAmount, ci.created_at AS createdAt
		 FROM cart_item ci JOIN commodity c ON c.id = ci.commodity_id
		 WHERE ci.member_id = ? ORDER BY ci.created_at DESC, ci.id DESC`,
		memberID,
	)
}

// cartItemByID 查询单个购物车条目，用于新增/更新后返回最新数据。
func (app *App) cartItemByID(r *http.Request, memberID, id int64) (map[string]any, error) {
	rows, err := app.queryMaps(
		r.Context(),
		`SELECT ci.id, ci.commodity_id AS commodityId, c.name AS commodityName,
		        c.category AS commodityCategory, c.price AS commodityPrice, c.stock AS commodityStock,
		        c.cover_image AS coverImage, ci.quantity, ci.selected,
		        (c.price * ci.quantity) AS subtotalAmount, ci.created_at AS createdAt
		 FROM cart_item ci JOIN commodity c ON c.id = ci.commodity_id
		 WHERE ci.member_id = ? AND ci.id = ? LIMIT 1`,
		memberID,
		id,
	)
	if err != nil {
		return nil, err
	}
	row, ok := firstRow(rows)
	if !ok {
		return nil, notFound("cart item does not exist")
	}
	return row, nil
}

// createOrder 根据购物车条目创建商品订单。
// 下单流程放在一个事务里：锁定购物车和商品库存、写入订单和订单明细、
// 扣减库存、删除已下单购物车项。任一步失败都会回滚，避免库存和订单不一致。
func (app *App) createOrder(w http.ResponseWriter, r *http.Request) error {
	user := currentAuthUser(r)
	body, err := decodeJSON(r)
	if err != nil {
		return err
	}
	rawIDs, ok := body["cartItemIds"].([]any)
	if !ok || len(rawIDs) == 0 {
		return badRequest("cartItemIds must not be empty")
	}
	cartIDs := make([]int64, 0, len(rawIDs))
	for _, raw := range rawIDs {
		id := int64(toInt(raw))
		if id <= 0 {
			return badRequest("cart item id is invalid")
		}
		cartIDs = append(cartIDs, id)
	}
	receiverName, err := requiredString(body, "receiverName")
	if err != nil {
		return err
	}
	receiverPhone, err := requiredString(body, "receiverPhone")
	if err != nil {
		return err
	}
	receiverAddress, err := requiredString(body, "receiverAddress")
	if err != nil {
		return err
	}

	tx, err := app.db.BeginTx(r.Context(), &sql.TxOptions{})
	if err != nil {
		return err
	}
	defer tx.Rollback()

	items, err := app.loadOwnedCartItemsTx(r.Context(), tx, user.UserID, cartIDs)
	if err != nil {
		return err
	}
	if len(items) != len(cartIDs) {
		return badRequest("some cart items do not belong to current user or do not exist")
	}

	total := 0.0
	for _, item := range items {
		if !strings.EqualFold(item.Status, "ON_SALE") {
			return badRequest("commodity is not available for sale")
		}
		if !item.Selected {
			return badRequest("all order cart items must be selected")
		}
		if item.Stock < item.Quantity {
			return badRequest("commodity stock is insufficient")
		}
		total += item.Price * float64(item.Quantity)
	}

	res, err := tx.ExecContext(
		r.Context(),
		`INSERT INTO commodity_order (
		    order_no, member_id, total_amount, pay_amount, status, payment_status,
		    receiver_name, receiver_phone, receiver_address
		 ) VALUES (?, ?, ?, ?, 'CREATED', 'UNPAID', ?, ?, ?)`,
		businessID("od"),
		user.UserID,
		total,
		total,
		receiverName,
		receiverPhone,
		receiverAddress,
	)
	if err != nil {
		return err
	}
	orderID, _ := res.LastInsertId()

	for _, item := range items {
		subtotal := item.Price * float64(item.Quantity)
		if _, err := tx.ExecContext(
			r.Context(),
			`INSERT INTO commodity_order_item (
			    order_id, commodity_id, commodity_name_snapshot, unit_price, quantity, subtotal_amount
			 ) VALUES (?, ?, ?, ?, ?, ?)`,
			orderID,
			item.CommodityID,
			item.CommodityName,
			item.Price,
			item.Quantity,
			subtotal,
		); err != nil {
			return err
		}
		res, err := tx.ExecContext(
			r.Context(),
			`UPDATE commodity SET stock = stock - ? WHERE id = ? AND stock >= ?`,
			item.Quantity,
			item.CommodityID,
			item.Quantity,
		)
		if err != nil {
			return err
		}
		affected, _ := res.RowsAffected()
		if affected == 0 {
			return badRequest("commodity stock is insufficient")
		}
	}
	for _, id := range cartIDs {
		if _, err := tx.ExecContext(r.Context(), `DELETE FROM cart_item WHERE id = ? AND member_id = ?`, id, user.UserID); err != nil {
			return err
		}
	}
	if err := tx.Commit(); err != nil {
		return err
	}

	detail, err := app.orderDetail(r, orderID, user)
	if err != nil {
		return err
	}
	return writeSuccess(w, detail)
}

// orderCartItem 是下单事务中从购物车和商品表读取出来的库存快照。
// 使用结构体而不是 map，方便在事务中做数量、状态和金额计算。
type orderCartItem struct {
	ID            int64
	CommodityID   int64
	CommodityName string
	Price         float64
	Stock         int
	Quantity      int
	Selected      bool
	Status        string
}

// loadOwnedCartItemsTx 在事务中读取当前会员拥有的购物车条目。
// SELECT ... FOR UPDATE 会锁住相关行，避免并发下单时出现重复扣库存或重复删除购物车项。
func (app *App) loadOwnedCartItemsTx(ctx context.Context, tx *sql.Tx, memberID int64, ids []int64) ([]orderCartItem, error) {
	placeholders := make([]string, len(ids))
	args := []any{memberID}
	for i, id := range ids {
		placeholders[i] = "?"
		args = append(args, id)
	}
	rows, err := tx.QueryContext(
		ctx,
		`SELECT ci.id, ci.commodity_id, c.name, c.price, c.stock, ci.quantity, ci.selected, c.status
		 FROM cart_item ci JOIN commodity c ON c.id = ci.commodity_id
		 WHERE ci.member_id = ? AND ci.id IN (`+strings.Join(placeholders, ",")+`)
		 FOR UPDATE`,
		args...,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []orderCartItem
	for rows.Next() {
		var item orderCartItem
		var selected int
		if err := rows.Scan(&item.ID, &item.CommodityID, &item.CommodityName, &item.Price, &item.Stock, &item.Quantity, &selected, &item.Status); err != nil {
			return nil, err
		}
		item.Selected = selected == 1
		items = append(items, item)
	}
	return items, rows.Err()
}

// listOrders 查询订单列表。
// 管理员能看所有订单，普通会员只能看自己的订单。
func (app *App) listOrders(w http.ResponseWriter, r *http.Request) error {
	user := currentAuthUser(r)
	query := `SELECT o.id, o.order_no AS orderNo, o.member_id AS memberId,
	                 m.username AS memberUsername, m.nickname AS memberDisplayName,
	                 o.total_amount AS totalAmount, o.pay_amount AS payAmount,
	                 o.status, o.payment_status AS paymentStatus, o.payment_time AS paymentTime,
	                 o.receiver_name AS receiverName, o.receiver_phone AS receiverPhone,
	                 o.receiver_address AS receiverAddress, o.created_at AS createdAt
	          FROM commodity_order o JOIN member m ON m.id = o.member_id`
	args := []any{}
	if user.UserType != "ADMIN" {
		query += " WHERE o.member_id = ?"
		args = append(args, user.UserID)
	}
	query += " ORDER BY o.created_at DESC, o.id DESC"
	rows, err := app.queryMaps(r.Context(), query, args...)
	if err != nil {
		return err
	}
	return writeSuccess(w, rows)
}

// getOrderDetail 查询订单详情入口。
func (app *App) getOrderDetail(w http.ResponseWriter, r *http.Request) error {
	user := currentAuthUser(r)
	id, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	detail, err := app.orderDetail(r, id, user)
	if err != nil {
		return err
	}
	return writeSuccess(w, detail)
}

// orderDetail 查询订单主表和明细表，并做会员本人可见性校验。
func (app *App) orderDetail(r *http.Request, orderID int64, user *AuthUser) (map[string]any, error) {
	rows, err := app.queryMaps(
		r.Context(),
		`SELECT o.id, o.order_no AS orderNo, o.member_id AS memberId,
		        m.username AS memberUsername, m.nickname AS memberDisplayName,
		        o.total_amount AS totalAmount, o.pay_amount AS payAmount,
		        o.status, o.payment_status AS paymentStatus, o.payment_time AS paymentTime,
		        o.receiver_name AS receiverName, o.receiver_phone AS receiverPhone,
		        o.receiver_address AS receiverAddress, o.created_at AS createdAt
		 FROM commodity_order o JOIN member m ON m.id = o.member_id
		 WHERE o.id = ? LIMIT 1`,
		orderID,
	)
	if err != nil {
		return nil, err
	}
	order, ok := firstRow(rows)
	if !ok {
		return nil, notFound("order does not exist")
	}
	if user.UserType != "ADMIN" && toInt(order["memberId"]) != int(user.UserID) {
		return nil, forbidden("you can only view your own orders")
	}
	items, err := app.queryMaps(
		r.Context(),
		`SELECT id, commodity_id AS commodityId, commodity_name_snapshot AS commodityNameSnapshot,
		        unit_price AS unitPrice, quantity, subtotal_amount AS subtotalAmount, created_at AS createdAt
		 FROM commodity_order_item WHERE order_id = ? ORDER BY id ASC`,
		orderID,
	)
	if err != nil {
		return nil, err
	}
	order["items"] = items
	return order, nil
}

// cancelOrder 取消当前会员自己的订单。
// 仅 CREATED + UNPAID 的订单允许取消。
func (app *App) cancelOrder(w http.ResponseWriter, r *http.Request) error {
	id, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	return app.cancelOrderByID(w, r, id)
}

// cancelOrderAlt 保留给旧接口路径的兼容入口。
func (app *App) cancelOrderAlt(w http.ResponseWriter, r *http.Request) error {
	id, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	return app.cancelOrderByID(w, r, id)
}

// cancelOrderByID 执行订单取消事务。
// 它会锁定订单行，确认归属和状态后调用 cancelUnpaidOrderTx 恢复库存。
func (app *App) cancelOrderByID(w http.ResponseWriter, r *http.Request, orderID int64) error {
	user := currentAuthUser(r)
	tx, err := app.db.BeginTx(r.Context(), nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	var memberID int64
	var status, paymentStatus string
	err = tx.QueryRowContext(
		r.Context(),
		`SELECT member_id, status, payment_status FROM commodity_order WHERE id = ? FOR UPDATE`,
		orderID,
	).Scan(&memberID, &status, &paymentStatus)
	if errors.Is(err, sql.ErrNoRows) {
		return notFound("order does not exist")
	}
	if err != nil {
		return err
	}
	if memberID != user.UserID {
		return forbidden("you can only cancel your own orders")
	}
	if status != "CREATED" || paymentStatus != "UNPAID" {
		return badRequest("current order cannot be canceled")
	}
	if err := app.cancelUnpaidOrderTx(r.Context(), tx, orderID); err != nil {
		return err
	}
	if err := tx.Commit(); err != nil {
		return err
	}
	return writeSuccess(w, nil)
}

// cancelUnpaidOrderTx 在已有事务中取消未支付订单并回补商品库存。
// 手动取消和超时取消都复用它，保证两条路径的库存逻辑一致。
func (app *App) cancelUnpaidOrderTx(ctx context.Context, tx *sql.Tx, orderID int64) error {
	res, err := tx.ExecContext(
		ctx,
		`UPDATE commodity_order SET status = 'CANCELED', payment_status = 'CANCELED'
		 WHERE id = ? AND status = 'CREATED' AND payment_status = 'UNPAID'`,
		orderID,
	)
	if err != nil {
		return err
	}
	affected, _ := res.RowsAffected()
	if affected == 0 {
		return badRequest("current order cannot be canceled")
	}
	rows, err := tx.QueryContext(ctx, `SELECT commodity_id, quantity FROM commodity_order_item WHERE order_id = ?`, orderID)
	if err != nil {
		return err
	}
	defer rows.Close()
	for rows.Next() {
		var commodityID int64
		var qty int
		if err := rows.Scan(&commodityID, &qty); err != nil {
			return err
		}
		if _, err := tx.ExecContext(ctx, `UPDATE commodity SET stock = stock + ? WHERE id = ?`, qty, commodityID); err != nil {
			return err
		}
	}
	return rows.Err()
}

// runOrderTimeoutScanner 定时扫描超时未支付订单。
// 它随后端进程启动，ctx 取消时自动退出。
func (app *App) runOrderTimeoutScanner(ctx context.Context) {
	ticker := time.NewTicker(app.cfg.OrderScanInterval)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			app.cancelExpiredOrders(ctx)
		}
	}
}

// cancelExpiredOrders 找出超过配置时长仍未支付的订单并逐个取消。
// 每个订单独立开事务，避免某一单失败影响其他订单回收库存。
func (app *App) cancelExpiredOrders(ctx context.Context) {
	cutoff := time.Now().Add(-app.cfg.OrderTimeout)
	rows, err := app.db.QueryContext(ctx, `SELECT id FROM commodity_order WHERE status = 'CREATED' AND payment_status = 'UNPAID' AND created_at < ?`, cutoff)
	if err != nil {
		return
	}
	var ids []int64
	for rows.Next() {
		var id int64
		if rows.Scan(&id) == nil {
			ids = append(ids, id)
		}
	}
	rows.Close()
	for _, id := range ids {
		tx, err := app.db.BeginTx(ctx, nil)
		if err != nil {
			continue
		}
		if err := app.cancelUnpaidOrderTx(ctx, tx, id); err != nil {
			_ = tx.Rollback()
			continue
		}
		_ = tx.Commit()
	}
}

// defaultString 在前端未传值时使用默认值。
func defaultString(value, fallback string) string {
	if strings.TrimSpace(value) == "" {
		return fallback
	}
	return value
}

// toInt 把各种 JSON/数据库返回值尽量转换为 int。
func toInt(value any) int {
	switch v := value.(type) {
	case nil:
		return 0
	case int:
		return v
	case int64:
		return int(v)
	case int32:
		return int(v)
	case float64:
		return int(v)
	case jsonNumber:
		i, _ := strconv.Atoi(v.String())
		return i
	case string:
		i, _ := strconv.Atoi(strings.TrimSpace(v))
		return i
	default:
		i, _ := strconv.Atoi(fmt.Sprint(v))
		return i
	}
}

// jsonNumber 抽象 json.Number，避免在 core_handlers.go 额外导入 encoding/json。
type jsonNumber interface {
	String() string
}

// asBool 把 JSON 值转换成 bool，主要用于购物车 selected 字段。
func asBool(value any, fallback bool) bool {
	switch v := value.(type) {
	case nil:
		return fallback
	case bool:
		return v
	case string:
		return strings.EqualFold(v, "true") || v == "1"
	case float64:
		return v != 0
	default:
		return fallback
	}
}
