// 文件作用：Go 后端的场馆预约和课程报名业务接口。
// 这里复现 Spring Boot 后端中健身房房间管理、会员预约、
// 课程管理、课程报名/取消以及后台报名查询相关功能。
// 预约和报名会涉及容量、时间冲突和状态校验，因此关键写操作都在事务中完成。
package main

import (
	"database/sql"
	"errors"
	"net/http"
	"strings"
	"time"
)

// listGymRooms 返回会员端可预约的房间，只展示 OPEN 状态房间。
func (app *App) listGymRooms(w http.ResponseWriter, r *http.Request) error {
	rows, err := app.queryMaps(
		r.Context(),
		`SELECT id, name, location, capacity,
		        TIME_FORMAT(open_time, '%H:%i:%s') AS openTime,
		        TIME_FORMAT(close_time, '%H:%i:%s') AS closeTime,
		        status, description
		 FROM gym_room WHERE status = 'OPEN' ORDER BY id DESC`,
	)
	if err != nil {
		return err
	}
	return writeSuccess(w, rows)
}

// getGymRoom 查询单个房间详情。
func (app *App) getGymRoom(w http.ResponseWriter, r *http.Request) error {
	id, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	row, err := app.gymRoomDetail(r, id)
	if err != nil {
		return err
	}
	return writeSuccess(w, row)
}

// gymRoomDetail 查询房间详情，并补充今天已预约人数和是否可预约。
func (app *App) gymRoomDetail(r *http.Request, id int64) (map[string]any, error) {
	rows, err := app.queryMaps(
		r.Context(),
		`SELECT id, name, location, capacity,
		        TIME_FORMAT(open_time, '%H:%i:%s') AS openTime,
		        TIME_FORMAT(close_time, '%H:%i:%s') AS closeTime,
		        status, description, created_at AS createdAt, updated_at AS updatedAt
		 FROM gym_room WHERE id = ? LIMIT 1`,
		id,
	)
	if err != nil {
		return nil, err
	}
	row, ok := firstRow(rows)
	if !ok {
		return nil, notFound("gym room does not exist")
	}
	today := time.Now().Format("2006-01-02")
	var booked int
	_ = app.db.QueryRowContext(
		r.Context(),
		`SELECT COALESCE(SUM(head_count), 0) FROM gym_booking WHERE gym_room_id = ? AND booking_date = ? AND status = 'CONFIRMED'`,
		id,
		today,
	).Scan(&booked)
	row["todayBookedHeadCount"] = booked
	row["bookable"] = strings.EqualFold(asString(row["status"]), "OPEN")
	return row, nil
}

// adminListGymRooms 管理员查看所有房间，包括 CLOSED 状态房间。
func (app *App) adminListGymRooms(w http.ResponseWriter, r *http.Request) error {
	rows, err := app.queryMaps(
		r.Context(),
		`SELECT id, name, location, capacity,
		        TIME_FORMAT(open_time, '%H:%i:%s') AS openTime,
		        TIME_FORMAT(close_time, '%H:%i:%s') AS closeTime,
		        status, description
		 FROM gym_room ORDER BY id DESC`,
	)
	if err != nil {
		return err
	}
	return writeSuccess(w, rows)
}

func (app *App) adminGetGymRoom(w http.ResponseWriter, r *http.Request) error {
	return app.getGymRoom(w, r)
}

// adminCreateGymRoom 新增健身房房间。
// openTime/closeTime 会统一规范成 HH:mm:ss，方便 MySQL TIME 字段保存。
func (app *App) adminCreateGymRoom(w http.ResponseWriter, r *http.Request) error {
	body, err := decodeJSON(r)
	if err != nil {
		return err
	}
	openTime, err := parseTimeOnly(asString(body["openTime"]))
	if err != nil {
		return badRequest("openTime is invalid")
	}
	closeTime, err := parseTimeOnly(asString(body["closeTime"]))
	if err != nil {
		return badRequest("closeTime is invalid")
	}
	res, err := app.db.ExecContext(
		r.Context(),
		`INSERT INTO gym_room (name, location, capacity, open_time, close_time, status, description)
		 VALUES (?, ?, ?, ?, ?, ?, ?)`,
		asString(body["name"]),
		nullableString(body, "location"),
		asInt(body, "capacity", 1),
		openTime,
		closeTime,
		defaultString(asString(body["status"]), "OPEN"),
		nullableString(body, "description"),
	)
	if err != nil {
		return err
	}
	id, _ := res.LastInsertId()
	row, err := app.gymRoomDetail(r, id)
	if err != nil {
		return err
	}
	return writeSuccess(w, row)
}

// adminUpdateGymRoom 更新房间基础信息、开放时间和状态。
func (app *App) adminUpdateGymRoom(w http.ResponseWriter, r *http.Request) error {
	id, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	body, err := decodeJSON(r)
	if err != nil {
		return err
	}
	openTime, err := parseTimeOnly(asString(body["openTime"]))
	if err != nil {
		return badRequest("openTime is invalid")
	}
	closeTime, err := parseTimeOnly(asString(body["closeTime"]))
	if err != nil {
		return badRequest("closeTime is invalid")
	}
	_, err = app.db.ExecContext(
		r.Context(),
		`UPDATE gym_room SET name = ?, location = ?, capacity = ?, open_time = ?, close_time = ?, status = ?, description = ? WHERE id = ?`,
		asString(body["name"]),
		nullableString(body, "location"),
		asInt(body, "capacity", 1),
		openTime,
		closeTime,
		defaultString(asString(body["status"]), "OPEN"),
		nullableString(body, "description"),
		id,
	)
	if err != nil {
		return err
	}
	row, err := app.gymRoomDetail(r, id)
	if err != nil {
		return err
	}
	return writeSuccess(w, row)
}

func (app *App) adminEnableGymRoom(w http.ResponseWriter, r *http.Request) error {
	return app.updateGymRoomStatus(w, r, "OPEN")
}

func (app *App) adminDisableGymRoom(w http.ResponseWriter, r *http.Request) error {
	return app.updateGymRoomStatus(w, r, "CLOSED")
}

// updateGymRoomStatus 切换房间 OPEN/CLOSED 状态。
func (app *App) updateGymRoomStatus(w http.ResponseWriter, r *http.Request, status string) error {
	id, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	_, err = app.db.ExecContext(r.Context(), `UPDATE gym_room SET status = ? WHERE id = ?`, status, id)
	if err != nil {
		return err
	}
	return writeSuccess(w, nil)
}

// createGymBooking 创建会员场馆预约。
// 事务中会锁定房间记录，校验开放状态、开放时间、会员个人时间冲突和房间容量。
func (app *App) createGymBooking(w http.ResponseWriter, r *http.Request) error {
	user := currentAuthUser(r)
	body, err := decodeJSON(r)
	if err != nil {
		return err
	}
	roomID := int64(asInt(body, "gymRoomId", 0))
	startTime, err := parseDateTime(asString(body["startTime"]))
	if err != nil {
		return badRequest("startTime is invalid")
	}
	endTime, err := parseDateTime(asString(body["endTime"]))
	if err != nil {
		return badRequest("endTime is invalid")
	}
	headCount := asInt(body, "headCount", 1)
	if roomID <= 0 || headCount <= 0 {
		return badRequest("gymRoomId and headCount are required")
	}
	if !startTime.Before(endTime) {
		return badRequest("start time must be earlier than end time")
	}
	if !startTime.After(time.Now()) {
		return badRequest("booking start time must be later than current time")
	}

	tx, err := app.db.BeginTx(r.Context(), nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()

	var capacity int
	var status, openTime, closeTime string
	err = tx.QueryRowContext(
		r.Context(),
		`SELECT capacity, status, COALESCE(TIME_FORMAT(open_time, '%H:%i:%s'), ''), COALESCE(TIME_FORMAT(close_time, '%H:%i:%s'), '')
		 FROM gym_room WHERE id = ? FOR UPDATE`,
		roomID,
	).Scan(&capacity, &status, &openTime, &closeTime)
	if errors.Is(err, sql.ErrNoRows) {
		return notFound("gym room does not exist")
	}
	if err != nil {
		return err
	}
	if status != "OPEN" {
		return badRequest("gym room is not open for booking")
	}
	if openTime != "" && closeTime != "" {
		startClock := startTime.Format("15:04:05")
		endClock := endTime.Format("15:04:05")
		if startClock < openTime || endClock > closeTime {
			return badRequest("booking time must be within gym room opening hours")
		}
	}
	conflicts, err := countRows(
		r.Context(),
		tx,
		`SELECT COUNT(1) FROM gym_booking
		 WHERE member_id = ? AND status = 'CONFIRMED' AND start_time < ? AND end_time > ?`,
		user.UserID,
		endTime,
		startTime,
	)
	if err != nil {
		return err
	}
	if conflicts > 0 {
		return badRequest("booking time conflicts with your existing booking")
	}
	booked, err := countRows(
		r.Context(),
		tx,
		`SELECT COALESCE(SUM(head_count), 0) FROM gym_booking
		 WHERE gym_room_id = ? AND status = 'CONFIRMED' AND start_time < ? AND end_time > ?`,
		roomID,
		endTime,
		startTime,
	)
	if err != nil {
		return err
	}
	if int(booked)+headCount > capacity {
		return badRequest("gym room capacity exceeded for the selected time slot")
	}
	duration := int(endTime.Sub(startTime).Minutes())
	res, err := tx.ExecContext(
		r.Context(),
		`INSERT INTO gym_booking (
		    booking_no, member_id, gym_room_id, booking_date, start_time, end_time,
		    duration_minutes, head_count, status, remark
		 ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'CONFIRMED', ?)`,
		businessID("bk"),
		user.UserID,
		roomID,
		startTime.Format("2006-01-02"),
		startTime,
		endTime,
		duration,
		headCount,
		nullableString(body, "remark"),
	)
	if err != nil {
		return err
	}
	id, _ := res.LastInsertId()
	if err := tx.Commit(); err != nil {
		return err
	}
	row, err := app.bookingDetail(r, id)
	if err != nil {
		return err
	}
	return writeSuccess(w, row)
}

// listMyBookings 查询当前会员自己的预约记录。
func (app *App) listMyBookings(w http.ResponseWriter, r *http.Request) error {
	user := currentAuthUser(r)
	rows, err := app.bookingRows(r, `gb.member_id = ?`, []any{user.UserID}, r.URL.Query().Get("status"))
	if err != nil {
		return err
	}
	return writeSuccess(w, rows)
}

// adminListBookings 管理员查询预约记录。
// 支持按预约号、会员账号、房间 ID 和状态过滤。
func (app *App) adminListBookings(w http.ResponseWriter, r *http.Request) error {
	q := r.URL.Query()
	where := []string{"1 = 1"}
	args := []any{}
	if v := strings.TrimSpace(q.Get("bookingNo")); v != "" {
		where = append(where, "gb.booking_no = ?")
		args = append(args, v)
	}
	if v := strings.TrimSpace(q.Get("memberUsername")); v != "" {
		where = append(where, "m.username = ?")
		args = append(args, v)
	}
	if v := strings.TrimSpace(q.Get("gymRoomId")); v != "" {
		where = append(where, "gb.gym_room_id = ?")
		args = append(args, v)
	}
	rows, err := app.bookingRows(r, strings.Join(where, " AND "), args, q.Get("status"))
	if err != nil {
		return err
	}
	return writeSuccess(w, rows)
}

// bookingRows 是预约列表/详情的公共查询方法。
// where 和 args 由调用方拼出，status 参数用于追加统一状态过滤。
func (app *App) bookingRows(r *http.Request, where string, args []any, status string) ([]map[string]any, error) {
	query := `SELECT gb.id, gb.booking_no AS bookingNo, gb.member_id AS memberId,
	                 m.username AS memberUsername, m.nickname AS memberDisplayName,
	                 gb.gym_room_id AS gymRoomId, gr.name AS gymRoomName,
	                 DATE_FORMAT(gb.booking_date, '%Y-%m-%d') AS bookingDate,
	                 gb.start_time AS startTime, gb.end_time AS endTime,
	                 gb.duration_minutes AS durationMinutes, gb.head_count AS headCount,
	                 gb.status, gb.remark, gb.created_at AS createdAt
	          FROM gym_booking gb
	          JOIN gym_room gr ON gr.id = gb.gym_room_id
	          JOIN member m ON m.id = gb.member_id
	          WHERE ` + where
	if strings.TrimSpace(status) != "" {
		query += " AND gb.status = ?"
		args = append(args, status)
	}
	query += " ORDER BY gb.created_at DESC, gb.id DESC"
	return app.queryMaps(r.Context(), query, args...)
}

// bookingDetail 查询单条预约详情。
func (app *App) bookingDetail(r *http.Request, id int64) (map[string]any, error) {
	rows, err := app.bookingRows(r, "gb.id = ?", []any{id}, "")
	if err != nil {
		return nil, err
	}
	row, ok := firstRow(rows)
	if !ok {
		return nil, notFound("booking record does not exist")
	}
	return row, nil
}

// cancelGymBooking 会员取消自己的预约。
func (app *App) cancelGymBooking(w http.ResponseWriter, r *http.Request) error {
	user := currentAuthUser(r)
	id, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	return app.cancelBooking(w, r, id, user.UserID)
}

// adminCancelGymBooking 管理员取消任意预约。
func (app *App) adminCancelGymBooking(w http.ResponseWriter, r *http.Request) error {
	id, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	return app.cancelBooking(w, r, id, 0)
}

// cancelBooking 执行预约取消逻辑。
// memberID=0 表示管理员操作；非 0 时必须验证该预约属于当前会员。
func (app *App) cancelBooking(w http.ResponseWriter, r *http.Request, id int64, memberID int64) error {
	var ownerID int64
	var status string
	var startTime time.Time
	err := app.db.QueryRowContext(r.Context(), `SELECT member_id, status, start_time FROM gym_booking WHERE id = ?`, id).Scan(&ownerID, &status, &startTime)
	if errors.Is(err, sql.ErrNoRows) {
		return notFound("booking record does not exist")
	}
	if err != nil {
		return err
	}
	if memberID != 0 && ownerID != memberID {
		return forbidden("you can only cancel your own booking")
	}
	if status != "CONFIRMED" {
		return badRequest("current booking cannot be canceled")
	}
	if !startTime.After(time.Now()) {
		return badRequest("booking that has started cannot be canceled")
	}
	_, err = app.db.ExecContext(r.Context(), `UPDATE gym_booking SET status = 'CANCELED' WHERE id = ?`, id)
	if err != nil {
		return err
	}
	return writeSuccess(w, nil)
}

// listCourses 查询课程列表。
// 会员账号如果未启用，会被限制访问课程业务，和预约业务保持一致。
func (app *App) listCourses(w http.ResponseWriter, r *http.Request) error {
	user := currentAuthUser(r)
	if user.UserType == "MEMBER" && user.Status != "ACTIVE" {
		return forbidden("member account is not enabled")
	}
	query := courseSelect() + ` WHERE 1 = 1`
	args := []any{}
	if status := strings.TrimSpace(r.URL.Query().Get("status")); status != "" {
		query += " AND c.status = ?"
		args = append(args, status)
	}
	query += " ORDER BY c.start_time ASC, c.id DESC"
	rows, err := app.queryMaps(r.Context(), query, args...)
	if err != nil {
		return err
	}
	return writeSuccess(w, rows)
}

// getCourse 查询课程详情。
func (app *App) getCourse(w http.ResponseWriter, r *http.Request) error {
	user := currentAuthUser(r)
	if user.UserType == "MEMBER" && user.Status != "ACTIVE" {
		return forbidden("member account is not enabled")
	}
	id, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	row, err := app.courseDetail(r, id)
	if err != nil {
		return err
	}
	return writeSuccess(w, row)
}

// courseSelect 返回课程查询的公共 SELECT 片段。
// 它同时关联教练 employee 和房间 gym_room，并计算已报名人数。
func courseSelect() string {
	return `SELECT c.id, c.name, c.course_type AS courseType, c.coach_id AS coachId,
	               e.name AS coachName, c.gym_room_id AS gymRoomId, gr.name AS gymRoomName,
	               c.start_time AS startTime, c.end_time AS endTime, c.capacity,
	               (SELECT COUNT(1) FROM course_enrollment ce WHERE ce.course_id = c.id AND ce.status = 'ENROLLED') AS enrolledCount,
	               c.price, c.description, c.status
	        FROM course c
	        LEFT JOIN employee e ON e.id = c.coach_id
	        LEFT JOIN gym_room gr ON gr.id = c.gym_room_id`
}

// courseDetail 查询课程详情，并补充 enrollable 字段供前端判断是否可报名。
func (app *App) courseDetail(r *http.Request, id int64) (map[string]any, error) {
	rows, err := app.queryMaps(r.Context(), courseSelect()+` WHERE c.id = ? LIMIT 1`, id)
	if err != nil {
		return nil, err
	}
	row, ok := firstRow(rows)
	if !ok {
		return nil, notFound("course does not exist")
	}
	start, _ := parseDateTime(asString(row["startTime"]))
	row["enrollable"] = strings.EqualFold(asString(row["status"]), "OPEN") && start.After(time.Now())
	return row, nil
}

// enrollCourse 会员报名课程。
// 事务中锁定课程行，检查课程状态、开始时间、容量以及是否已报名，防止并发超额报名。
func (app *App) enrollCourse(w http.ResponseWriter, r *http.Request) error {
	user := currentAuthUser(r)
	courseID, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	tx, err := app.db.BeginTx(r.Context(), nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	var capacity int
	var status string
	var startTime time.Time
	err = tx.QueryRowContext(r.Context(), `SELECT capacity, status, start_time FROM course WHERE id = ? FOR UPDATE`, courseID).Scan(&capacity, &status, &startTime)
	if errors.Is(err, sql.ErrNoRows) {
		return notFound("course does not exist")
	}
	if err != nil {
		return err
	}
	if status != "OPEN" {
		return badRequest("course is not open for enrollment")
	}
	if !startTime.After(time.Now()) {
		return badRequest("course has already started")
	}
	enrolled, err := countRows(r.Context(), tx, `SELECT COUNT(1) FROM course_enrollment WHERE course_id = ? AND status = 'ENROLLED'`, courseID)
	if err != nil {
		return err
	}
	if int(enrolled) >= capacity {
		return badRequest("course capacity is full")
	}
	var existingID int64
	var existingStatus string
	err = tx.QueryRowContext(
		r.Context(),
		`SELECT id, status FROM course_enrollment WHERE member_id = ? AND course_id = ? LIMIT 1`,
		user.UserID,
		courseID,
	).Scan(&existingID, &existingStatus)
	if err == nil {
		if existingStatus == "ENROLLED" {
			return badRequest("you have already enrolled in this course")
		}
		_, err = tx.ExecContext(r.Context(), `UPDATE course_enrollment SET status = 'ENROLLED' WHERE id = ?`, existingID)
	} else if errors.Is(err, sql.ErrNoRows) {
		_, err = tx.ExecContext(
			r.Context(),
			`INSERT INTO course_enrollment (enrollment_no, member_id, course_id, status) VALUES (?, ?, ?, 'ENROLLED')`,
			businessID("en"),
			user.UserID,
			courseID,
		)
	} else {
		return err
	}
	if err != nil {
		return err
	}
	if err := tx.Commit(); err != nil {
		return err
	}
	rows, err := app.myCourseRows(r, user.UserID, "ENROLLED")
	if err != nil {
		return err
	}
	for _, row := range rows {
		if int64(toInt(row["courseId"])) == courseID {
			return writeSuccess(w, row)
		}
	}
	return badRequest("failed to load enrollment result")
}

// listMyCourses 查询当前会员自己的课程报名记录。
func (app *App) listMyCourses(w http.ResponseWriter, r *http.Request) error {
	user := currentAuthUser(r)
	rows, err := app.myCourseRows(r, user.UserID, r.URL.Query().Get("status"))
	if err != nil {
		return err
	}
	return writeSuccess(w, rows)
}

// myCourseRows 查询某个会员的课程报名列表，并可按报名状态过滤。
func (app *App) myCourseRows(r *http.Request, memberID int64, status string) ([]map[string]any, error) {
	query := `SELECT ce.id AS enrollmentId, ce.enrollment_no AS enrollmentNo, ce.status AS enrollmentStatus,
	                 c.id AS courseId, c.name AS courseName, c.course_type AS courseType,
	                 e.name AS coachName, gr.name AS gymRoomName,
	                 c.start_time AS startTime, c.end_time AS endTime, c.price, ce.created_at AS createdAt
	          FROM course_enrollment ce
	          JOIN course c ON c.id = ce.course_id
	          LEFT JOIN employee e ON e.id = c.coach_id
	          LEFT JOIN gym_room gr ON gr.id = c.gym_room_id
	          WHERE ce.member_id = ?`
	args := []any{memberID}
	if strings.TrimSpace(status) != "" {
		query += " AND ce.status = ?"
		args = append(args, status)
	}
	query += " ORDER BY ce.created_at DESC, ce.id DESC"
	return app.queryMaps(r.Context(), query, args...)
}

// cancelEnrollment 会员取消自己的课程报名。
func (app *App) cancelEnrollment(w http.ResponseWriter, r *http.Request) error {
	user := currentAuthUser(r)
	id, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	return app.cancelEnrollmentByID(w, r, id, user.UserID)
}

// adminCancelEnrollment 管理员取消任意课程报名。
func (app *App) adminCancelEnrollment(w http.ResponseWriter, r *http.Request) error {
	id, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	return app.cancelEnrollmentByID(w, r, id, 0)
}

// cancelEnrollmentByID 执行课程报名取消逻辑。
// 已开始的课程不允许取消；memberID=0 表示管理员操作。
func (app *App) cancelEnrollmentByID(w http.ResponseWriter, r *http.Request, enrollmentID int64, memberID int64) error {
	var ownerID int64
	var courseID int64
	var status string
	err := app.db.QueryRowContext(r.Context(), `SELECT member_id, course_id, status FROM course_enrollment WHERE id = ?`, enrollmentID).Scan(&ownerID, &courseID, &status)
	if errors.Is(err, sql.ErrNoRows) {
		return notFound("course enrollment does not exist")
	}
	if err != nil {
		return err
	}
	if memberID != 0 && ownerID != memberID {
		return forbidden("you can only cancel your own course enrollment")
	}
	if status != "ENROLLED" {
		return badRequest("current course enrollment cannot be canceled")
	}
	var startTime time.Time
	if err := app.db.QueryRowContext(r.Context(), `SELECT start_time FROM course WHERE id = ?`, courseID).Scan(&startTime); err != nil {
		return err
	}
	if !startTime.After(time.Now()) {
		return badRequest("course that has started cannot be canceled")
	}
	_, err = app.db.ExecContext(r.Context(), `UPDATE course_enrollment SET status = 'CANCELED' WHERE id = ?`, enrollmentID)
	if err != nil {
		return err
	}
	return writeSuccess(w, nil)
}

// adminCreateCourse 管理员新增课程。
// 课程开始时间必须早于结束时间，容量默认 20。
func (app *App) adminCreateCourse(w http.ResponseWriter, r *http.Request) error {
	body, err := decodeJSON(r)
	if err != nil {
		return err
	}
	startTime, err := parseDateTime(asString(body["startTime"]))
	if err != nil {
		return badRequest("startTime is invalid")
	}
	endTime, err := parseDateTime(asString(body["endTime"]))
	if err != nil {
		return badRequest("endTime is invalid")
	}
	if !startTime.Before(endTime) {
		return badRequest("course start time must be earlier than end time")
	}
	res, err := app.db.ExecContext(
		r.Context(),
		`INSERT INTO course (name, coach_id, gym_room_id, course_type, start_time, end_time, capacity, price, description, status)
		 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
		asString(body["name"]),
		nullableString(body, "coachId"),
		nullableString(body, "gymRoomId"),
		nullableString(body, "courseType"),
		startTime,
		endTime,
		asInt(body, "capacity", 20),
		nullableString(body, "price"),
		nullableString(body, "description"),
		defaultString(asString(body["status"]), "OPEN"),
	)
	if err != nil {
		return err
	}
	id, _ := res.LastInsertId()
	row, err := app.courseDetail(r, id)
	if err != nil {
		return err
	}
	return writeSuccess(w, row)
}

// adminUpdateCourse 管理员更新课程信息。
func (app *App) adminUpdateCourse(w http.ResponseWriter, r *http.Request) error {
	id, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	body, err := decodeJSON(r)
	if err != nil {
		return err
	}
	startTime, err := parseDateTime(asString(body["startTime"]))
	if err != nil {
		return badRequest("startTime is invalid")
	}
	endTime, err := parseDateTime(asString(body["endTime"]))
	if err != nil {
		return badRequest("endTime is invalid")
	}
	if !startTime.Before(endTime) {
		return badRequest("course start time must be earlier than end time")
	}
	_, err = app.db.ExecContext(
		r.Context(),
		`UPDATE course SET name = ?, coach_id = ?, gym_room_id = ?, course_type = ?, start_time = ?, end_time = ?,
		                   capacity = ?, price = ?, description = ?, status = ? WHERE id = ?`,
		asString(body["name"]),
		nullableString(body, "coachId"),
		nullableString(body, "gymRoomId"),
		nullableString(body, "courseType"),
		startTime,
		endTime,
		asInt(body, "capacity", 20),
		nullableString(body, "price"),
		nullableString(body, "description"),
		defaultString(asString(body["status"]), "OPEN"),
		id,
	)
	if err != nil {
		return err
	}
	row, err := app.courseDetail(r, id)
	if err != nil {
		return err
	}
	return writeSuccess(w, row)
}

func (app *App) adminEnableCourse(w http.ResponseWriter, r *http.Request) error {
	return app.updateCourseStatus(w, r, "OPEN")
}

func (app *App) adminDisableCourse(w http.ResponseWriter, r *http.Request) error {
	return app.updateCourseStatus(w, r, "CLOSED")
}

// updateCourseStatus 切换课程 OPEN/CLOSED 状态。
func (app *App) updateCourseStatus(w http.ResponseWriter, r *http.Request, status string) error {
	id, err := asInt64Path(r, "id")
	if err != nil {
		return err
	}
	_, err = app.db.ExecContext(r.Context(), `UPDATE course SET status = ? WHERE id = ?`, status, id)
	if err != nil {
		return err
	}
	return writeSuccess(w, nil)
}

// adminListEnrollments 管理员查询所有课程报名记录。
// 支持按报名号、会员账号、课程 ID 和报名状态过滤。
func (app *App) adminListEnrollments(w http.ResponseWriter, r *http.Request) error {
	q := r.URL.Query()
	query := `SELECT ce.id AS enrollmentId, ce.enrollment_no AS enrollmentNo, ce.status AS enrollmentStatus,
	                 m.id AS memberId, m.username AS memberUsername, m.nickname AS memberDisplayName,
	                 c.id AS courseId, c.name AS courseName, c.course_type AS courseType,
	                 e.name AS coachName, gr.name AS gymRoomName,
	                 c.start_time AS startTime, c.end_time AS endTime, c.price, ce.created_at AS createdAt
	          FROM course_enrollment ce
	          JOIN member m ON m.id = ce.member_id
	          JOIN course c ON c.id = ce.course_id
	          LEFT JOIN employee e ON e.id = c.coach_id
	          LEFT JOIN gym_room gr ON gr.id = c.gym_room_id
	          WHERE 1 = 1`
	args := []any{}
	if v := strings.TrimSpace(q.Get("enrollmentNo")); v != "" {
		query += " AND ce.enrollment_no = ?"
		args = append(args, v)
	}
	if v := strings.TrimSpace(q.Get("memberUsername")); v != "" {
		query += " AND m.username = ?"
		args = append(args, v)
	}
	if v := strings.TrimSpace(q.Get("courseId")); v != "" {
		query += " AND ce.course_id = ?"
		args = append(args, v)
	}
	if v := strings.TrimSpace(q.Get("status")); v != "" {
		query += " AND ce.status = ?"
		args = append(args, v)
	}
	query += " ORDER BY ce.created_at DESC, ce.id DESC"
	rows, err := app.queryMaps(r.Context(), query, args...)
	if err != nil {
		return err
	}
	return writeSuccess(w, rows)
}
