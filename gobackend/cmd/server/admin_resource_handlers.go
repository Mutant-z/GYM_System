// 文件作用：Go 后端的后台资源管理接口。
// 这里负责管理员对员工 employee 和器材 equipment 的增删改查式管理，
// 这些接口只挂在 /api/admin/... 路径下，并由 main.go 的 requireAdmin 统一鉴权。
package main

import "net/http"

// adminListEmployees 查询员工列表。
func (app *App) adminListEmployees(w http.ResponseWriter, r *http.Request) error {
	rows, err := app.queryMaps(
		r.Context(),
		`SELECT id, name, phone, gender, position, specialty,
		        DATE_FORMAT(hire_date, '%Y-%m-%d') AS hireDate,
		        status, created_at AS createdAt, updated_at AS updatedAt
		 FROM employee ORDER BY id DESC`,
	)
	if err != nil {
		return err
	}
	return writeSuccess(w, rows)
}

// adminGetEmployee 查询单个员工详情。
func (app *App) adminGetEmployee(w http.ResponseWriter, r *http.Request) error {
	id, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	row, err := app.employeeDetail(r, id)
	if err != nil {
		return err
	}
	return writeSuccess(w, row)
}

// employeeDetail 是员工详情公共查询方法，创建/更新后也会复用它返回最新记录。
func (app *App) employeeDetail(r *http.Request, id int64) (map[string]any, error) {
	rows, err := app.queryMaps(
		r.Context(),
		`SELECT id, name, phone, gender, position, specialty,
		        DATE_FORMAT(hire_date, '%Y-%m-%d') AS hireDate,
		        status, created_at AS createdAt, updated_at AS updatedAt
		 FROM employee WHERE id = ? LIMIT 1`,
		id,
	)
	if err != nil {
		return nil, err
	}
	row, ok := firstRow(rows)
	if !ok {
		return nil, notFound("employee does not exist")
	}
	return row, nil
}

// adminCreateEmployee 新增员工或教练。
// hireDate 会做日期格式校验，status 未传时默认 ACTIVE。
func (app *App) adminCreateEmployee(w http.ResponseWriter, r *http.Request) error {
	body, err := decodeJSON(r)
	if err != nil {
		return err
	}
	hireDate, err := parseDate(asString(body["hireDate"]))
	if err != nil {
		return badRequest("hireDate is invalid")
	}
	res, err := app.db.ExecContext(
		r.Context(),
		`INSERT INTO employee (name, phone, gender, position, specialty, hire_date, status)
		 VALUES (?, ?, ?, ?, ?, ?, ?)`,
		asString(body["name"]),
		nullableString(body, "phone"),
		nullableString(body, "gender"),
		asString(body["position"]),
		nullableString(body, "specialty"),
		hireDate,
		defaultString(asString(body["status"]), "ACTIVE"),
	)
	if err != nil {
		return err
	}
	id, _ := res.LastInsertId()
	row, err := app.employeeDetail(r, id)
	if err != nil {
		return err
	}
	return writeSuccess(w, row)
}

// adminUpdateEmployee 更新员工基础资料。
func (app *App) adminUpdateEmployee(w http.ResponseWriter, r *http.Request) error {
	id, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	body, err := decodeJSON(r)
	if err != nil {
		return err
	}
	hireDate, err := parseDate(asString(body["hireDate"]))
	if err != nil {
		return badRequest("hireDate is invalid")
	}
	_, err = app.db.ExecContext(
		r.Context(),
		`UPDATE employee SET name = ?, phone = ?, gender = ?, position = ?, specialty = ?, hire_date = ?, status = ? WHERE id = ?`,
		asString(body["name"]),
		nullableString(body, "phone"),
		nullableString(body, "gender"),
		asString(body["position"]),
		nullableString(body, "specialty"),
		hireDate,
		defaultString(asString(body["status"]), "ACTIVE"),
		id,
	)
	if err != nil {
		return err
	}
	row, err := app.employeeDetail(r, id)
	if err != nil {
		return err
	}
	return writeSuccess(w, row)
}

func (app *App) adminEnableEmployee(w http.ResponseWriter, r *http.Request) error {
	return app.updateEmployeeStatus(w, r, "ACTIVE")
}

func (app *App) adminDisableEmployee(w http.ResponseWriter, r *http.Request) error {
	return app.updateEmployeeStatus(w, r, "DISABLED")
}

// updateEmployeeStatus 启用/停用员工。
// 课程教练列表是否展示停用员工，由前端或后续查询条件决定。
func (app *App) updateEmployeeStatus(w http.ResponseWriter, r *http.Request, status string) error {
	id, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	_, err = app.db.ExecContext(r.Context(), `UPDATE employee SET status = ? WHERE id = ?`, status, id)
	if err != nil {
		return err
	}
	return writeSuccess(w, nil)
}

// adminListEquipments 查询器材列表，并关联房间名称，便于后台表格展示。
func (app *App) adminListEquipments(w http.ResponseWriter, r *http.Request) error {
	rows, err := app.queryMaps(
		r.Context(),
		`SELECT e.id, e.gym_room_id AS gymRoomId, gr.name AS gymRoomName,
		        e.name, e.category, e.brand, e.quantity, e.status,
		        DATE_FORMAT(e.purchase_date, '%Y-%m-%d') AS purchaseDate,
		        e.description, e.created_at AS createdAt, e.updated_at AS updatedAt
		 FROM equipment e LEFT JOIN gym_room gr ON gr.id = e.gym_room_id
		 ORDER BY e.id DESC`,
	)
	if err != nil {
		return err
	}
	return writeSuccess(w, rows)
}

// adminGetEquipment 查询单个器材详情。
func (app *App) adminGetEquipment(w http.ResponseWriter, r *http.Request) error {
	id, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	row, err := app.equipmentDetail(r, id)
	if err != nil {
		return err
	}
	return writeSuccess(w, row)
}

// equipmentDetail 是器材详情公共查询方法，创建/更新后也会复用它返回最新记录。
func (app *App) equipmentDetail(r *http.Request, id int64) (map[string]any, error) {
	rows, err := app.queryMaps(
		r.Context(),
		`SELECT id, gym_room_id AS gymRoomId, name, category, brand, quantity, status,
		        DATE_FORMAT(purchase_date, '%Y-%m-%d') AS purchaseDate,
		        description, created_at AS createdAt, updated_at AS updatedAt
		 FROM equipment WHERE id = ? LIMIT 1`,
		id,
	)
	if err != nil {
		return nil, err
	}
	row, ok := firstRow(rows)
	if !ok {
		return nil, notFound("equipment does not exist")
	}
	return row, nil
}

// adminCreateEquipment 新增器材。
// gymRoomId 允许为空，表示器材暂未绑定具体房间。
func (app *App) adminCreateEquipment(w http.ResponseWriter, r *http.Request) error {
	body, err := decodeJSON(r)
	if err != nil {
		return err
	}
	purchaseDate, err := parseDate(asString(body["purchaseDate"]))
	if err != nil {
		return badRequest("purchaseDate is invalid")
	}
	res, err := app.db.ExecContext(
		r.Context(),
		`INSERT INTO equipment (gym_room_id, name, category, brand, quantity, status, purchase_date, description)
		 VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
		nullableString(body, "gymRoomId"),
		asString(body["name"]),
		nullableString(body, "category"),
		nullableString(body, "brand"),
		asInt(body, "quantity", 1),
		defaultString(asString(body["status"]), "AVAILABLE"),
		purchaseDate,
		nullableString(body, "description"),
	)
	if err != nil {
		return err
	}
	id, _ := res.LastInsertId()
	row, err := app.equipmentDetail(r, id)
	if err != nil {
		return err
	}
	return writeSuccess(w, row)
}

// adminUpdateEquipment 更新器材基础信息和所属房间。
func (app *App) adminUpdateEquipment(w http.ResponseWriter, r *http.Request) error {
	id, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	body, err := decodeJSON(r)
	if err != nil {
		return err
	}
	purchaseDate, err := parseDate(asString(body["purchaseDate"]))
	if err != nil {
		return badRequest("purchaseDate is invalid")
	}
	_, err = app.db.ExecContext(
		r.Context(),
		`UPDATE equipment SET gym_room_id = ?, name = ?, category = ?, brand = ?, quantity = ?, status = ?, purchase_date = ?, description = ? WHERE id = ?`,
		nullableString(body, "gymRoomId"),
		asString(body["name"]),
		nullableString(body, "category"),
		nullableString(body, "brand"),
		asInt(body, "quantity", 1),
		defaultString(asString(body["status"]), "AVAILABLE"),
		purchaseDate,
		nullableString(body, "description"),
		id,
	)
	if err != nil {
		return err
	}
	row, err := app.equipmentDetail(r, id)
	if err != nil {
		return err
	}
	return writeSuccess(w, row)
}

func (app *App) adminEnableEquipment(w http.ResponseWriter, r *http.Request) error {
	return app.updateEquipmentStatus(w, r, "AVAILABLE")
}

func (app *App) adminDisableEquipment(w http.ResponseWriter, r *http.Request) error {
	return app.updateEquipmentStatus(w, r, "DISABLED")
}

// updateEquipmentStatus 切换器材 AVAILABLE/DISABLED 状态。
func (app *App) updateEquipmentStatus(w http.ResponseWriter, r *http.Request, status string) error {
	id, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	_, err = app.db.ExecContext(r.Context(), `UPDATE equipment SET status = ? WHERE id = ?`, status, id)
	if err != nil {
		return err
	}
	return writeSuccess(w, nil)
}
