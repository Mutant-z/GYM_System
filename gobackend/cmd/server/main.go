// 文件作用：Go 后端的主入口和公共基础设施。
// 这里负责读取配置、连接 MySQL、注册 HTTP 路由、挂载中间件、
// 管理登录 token，并提供 JSON 响应、参数解析、SQL 查询映射等通用工具。
// 会员/商品/订单等核心业务在 core_handlers.go，
// 场馆预约/课程报名业务在 schedule_handlers.go，
// 员工/器材等后台资源管理在 admin_resource_handlers.go。
package main

import (
	"bytes"
	"context"
	"crypto/rand"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"math"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"time"

	_ "github.com/go-sql-driver/mysql"
	"golang.org/x/crypto/bcrypt"
)

// Config 是整个 Go 后端的运行配置。
// 默认值会先在 LoadConfig 中给出，然后被 config.yaml 和环境变量覆盖。
type Config struct {
	ServerPort          int           // Go 后端监听端口，默认 8080，可用 SERVER_PORT 覆盖。
	APIPrefix           string        // API 前缀，默认 /api，用来保持和原 Spring Boot 接口路径一致。
	MySQLHost           string        // gym_system 数据库地址。
	MySQLPort           int           // MySQL 端口。
	MySQLDatabase       string        // 数据库名，默认 gym_system。
	MySQLUsername       string        // 数据库用户名。
	MySQLPassword       string        // 数据库密码。
	AgentBaseURL        string        // Python Agent 服务地址，/api/chat 会转发到这里。
	AgentRequestTimeout time.Duration // 调用 Agent 的 HTTP 超时时间。
	OrderTimeout        time.Duration // 未支付订单的自动取消时长。
	OrderScanInterval   time.Duration // 后台扫描未支付订单的间隔。
	AuthTokenTTL        time.Duration // 内存 token 的续期时间。
	FrontendEnabled     bool          // 是否在启动 Go 后端时自动启动 Vite 前端。
	FrontendWorkingDir  string        // 前端项目工作目录。
	FrontendCommand     string        // 前端启动命令。
}

// App 是 handler 的依赖容器。
// 所有路由方法都挂在 App 上，从而共享配置、数据库连接、token 仓库和 HTTP 客户端。
type App struct {
	cfg    Config       // 当前服务配置。
	db     *sql.DB      // 连接同一个 gym_system MySQL 数据库。
	tokens *TokenStore  // 轻量内存 token 仓库，当前用于平替 Spring Security/Redis 的登录态。
	client *http.Client // 复用的 HTTP 客户端，主要用于转发 Python Agent。
}

// APIResponse 统一前后端响应格式。
// code=0 表示成功，非 0 时 message 会给出业务错误原因。
type APIResponse struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
	Data    any    `json:"data"`
}

// AppError 表示可直接返回给前端的业务错误。
// wrap 会把普通 error 统一转换成 500，只有 AppError 会保留自己的 HTTP 状态码和业务 code。
type AppError struct {
	Status  int
	Code    int
	Message string
}

func (e *AppError) Error() string {
	return e.Message
}

// HandlerFunc 是本项目内部使用的 handler 形式。
// 相比标准 http.HandlerFunc，多返回一个 error，方便集中做 JSON 错误响应。
type HandlerFunc func(http.ResponseWriter, *http.Request) error

// AuthUser 是登录后写入 token 的最小用户信息。
// 会员和管理员共用这一个结构，靠 UserType/Role/Status 区分权限和状态。
type AuthUser struct {
	UserID      int64  `json:"userId"`
	Username    string `json:"username"`
	DisplayName string `json:"displayName"`
	UserType    string `json:"userType"`
	Role        string `json:"role"`
	Status      string `json:"status"`
	LoginAt     string `json:"loginAt,omitempty"`
}

type contextKey string

// authContextKey 用于把 requireAuth 解析出的用户放入 request context。
const authContextKey contextKey = "authUser"

// main 是服务启动流程：
// 1. 读取配置并连接 MySQL；
// 2. 初始化 App 依赖和默认管理员；
// 3. 启动订单超时扫描、前端 dev server；
// 4. 启动 HTTP 服务，并在收到系统信号时优雅关闭。
func main() {
	cfg, err := LoadConfig()
	if err != nil {
		log.Fatalf("load config: %v", err)
	}

	// Go 后端直接复用 Spring Boot 项目当前的 gym_system 数据库。
	db, err := sql.Open("mysql", cfg.mysqlDSN())
	if err != nil {
		log.Fatalf("open mysql: %v", err)
	}
	// 设置连接池，避免开发测试时频繁创建连接，也避免无限打开连接拖垮 MySQL。
	db.SetMaxOpenConns(20)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(20 * time.Minute)
	if err := db.Ping(); err != nil {
		log.Fatalf("ping mysql: %v", err)
	}

	app := &App{
		cfg:    cfg,
		db:     db,
		tokens: NewTokenStore(cfg.AuthTokenTTL),
		client: &http.Client{Timeout: cfg.AgentRequestTimeout},
	}
	// 如果数据库里还没有默认管理员，则插入 admin001/123456，方便首次测试。
	app.ensureDefaultAdmin()

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	// 后台任务和前端进程都挂在同一个 ctx 下，后端退出时它们会一起停止。
	go app.runOrderTimeoutScanner(ctx)
	go startFrontendDevServer(ctx, cfg)

	server := &http.Server{
		Addr:              fmt.Sprintf(":%d", cfg.ServerPort),
		Handler:           app.routes(),
		ReadHeaderTimeout: 10 * time.Second,
	}

	go func() {
		log.Printf("Go backend listening on http://localhost:%d%s", cfg.ServerPort, cfg.APIPrefix)
		if err := server.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			log.Fatalf("listen: %v", err)
		}
	}()

	<-ctx.Done()
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	_ = server.Shutdown(shutdownCtx)
	_ = db.Close()
}

// LoadConfig 读取 Go 后端配置。
// 配置优先级：默认值 < config.yaml < 环境变量。
// 这样既能保持本地开发开箱即用，也方便临时用 SERVER_PORT=8081 这类方式覆盖。
func LoadConfig() (Config, error) {
	cfg := Config{
		ServerPort:          8080,
		APIPrefix:           "/api",
		MySQLHost:           "localhost",
		MySQLPort:           3306,
		MySQLDatabase:       "gym_system",
		MySQLUsername:       "root",
		MySQLPassword:       "mt94591845",
		AgentBaseURL:        "http://localhost:8000",
		AgentRequestTimeout: 180 * time.Second,
		OrderTimeout:        15 * time.Minute,
		OrderScanInterval:   60 * time.Second,
		AuthTokenTTL:        24 * time.Hour,
		FrontendEnabled:     true,
		FrontendWorkingDir:  "../frontend",
		FrontendCommand:     "npm run dev -- --host 0.0.0.0 --port 5173 --strictPort",
	}

	path := os.Getenv("GYM_GO_CONFIG")
	if path == "" {
		path = filepath.Join(".", "config.yaml")
	}
	if b, err := os.ReadFile(path); err == nil {
		applySimpleYAML(&cfg, string(b))
	} else if !os.IsNotExist(err) {
		return cfg, err
	}

	if v := os.Getenv("SERVER_PORT"); v != "" {
		cfg.ServerPort = mustInt(v, cfg.ServerPort)
	}
	if v := os.Getenv("MYSQL_HOST"); v != "" {
		cfg.MySQLHost = v
	}
	if v := os.Getenv("MYSQL_PORT"); v != "" {
		cfg.MySQLPort = mustInt(v, cfg.MySQLPort)
	}
	if v := os.Getenv("MYSQL_DATABASE"); v != "" {
		cfg.MySQLDatabase = v
	}
	if v := os.Getenv("MYSQL_USERNAME"); v != "" {
		cfg.MySQLUsername = v
	}
	if v := os.Getenv("MYSQL_PASSWORD"); v != "" {
		cfg.MySQLPassword = v
	}
	if v := os.Getenv("AGENT_BASE_URL"); v != "" {
		cfg.AgentBaseURL = v
	}
	if v := os.Getenv("FRONTEND_ENABLED"); v != "" {
		cfg.FrontendEnabled = strings.EqualFold(v, "true")
	}
	if v := os.Getenv("FRONTEND_WORKING_DIRECTORY"); v != "" {
		cfg.FrontendWorkingDir = v
	}
	if v := os.Getenv("FRONTEND_COMMAND"); v != "" {
		cfg.FrontendCommand = v
	}

	cfg.APIPrefix = "/" + strings.Trim(cfg.APIPrefix, "/")
	cfg.AgentBaseURL = strings.TrimRight(cfg.AgentBaseURL, "/")
	return cfg, nil
}

// applySimpleYAML 解析本项目 config.yaml 中用到的简单二级 YAML。
// 为了减少额外依赖，这里只支持当前配置文件需要的 key:value 和 section:key 形式；
// 如果后续配置变复杂，可以替换成正式 YAML 库。
func applySimpleYAML(cfg *Config, content string) {
	section := ""
	for _, raw := range strings.Split(content, "\n") {
		line := strings.TrimRight(raw, " \t")
		if strings.TrimSpace(line) == "" || strings.HasPrefix(strings.TrimSpace(line), "#") {
			continue
		}
		if !strings.HasPrefix(line, " ") && strings.HasSuffix(strings.TrimSpace(line), ":") {
			section = strings.TrimSuffix(strings.TrimSpace(line), ":")
			continue
		}
		parts := strings.SplitN(strings.TrimSpace(line), ":", 2)
		if len(parts) != 2 {
			continue
		}
		key := strings.TrimSpace(parts[0])
		value := strings.Trim(strings.TrimSpace(parts[1]), `"'`)
		switch section + "." + key {
		case "server.port":
			cfg.ServerPort = mustInt(value, cfg.ServerPort)
		case "server.api_prefix":
			cfg.APIPrefix = value
		case "mysql.host":
			cfg.MySQLHost = value
		case "mysql.port":
			cfg.MySQLPort = mustInt(value, cfg.MySQLPort)
		case "mysql.database":
			cfg.MySQLDatabase = value
		case "mysql.username":
			cfg.MySQLUsername = value
		case "mysql.password":
			cfg.MySQLPassword = value
		case "agent.base_url":
			cfg.AgentBaseURL = value
		case "agent.request_timeout_seconds":
			cfg.AgentRequestTimeout = time.Duration(mustInt(value, 180)) * time.Second
		case "order.timeout_minutes":
			cfg.OrderTimeout = time.Duration(mustInt(value, 15)) * time.Minute
		case "order.timeout_scan_interval_seconds":
			cfg.OrderScanInterval = time.Duration(mustInt(value, 60)) * time.Second
		case "auth.token_ttl_hours":
			cfg.AuthTokenTTL = time.Duration(mustInt(value, 24)) * time.Hour
		case "frontend.enabled":
			cfg.FrontendEnabled = strings.EqualFold(value, "true")
		case "frontend.working_directory":
			cfg.FrontendWorkingDir = value
		case "frontend.command":
			cfg.FrontendCommand = value
		}
	}
}

// mysqlDSN 拼出 go-sql-driver/mysql 需要的连接串。
// parseTime=true 让 MySQL DATETIME/TIMESTAMP 可以直接扫描成 time.Time。
func (c Config) mysqlDSN() string {
	return fmt.Sprintf(
		"%s:%s@tcp(%s:%d)/%s?charset=utf8mb4&parseTime=true&loc=Local&multiStatements=false",
		c.MySQLUsername,
		c.MySQLPassword,
		c.MySQLHost,
		c.MySQLPort,
		c.MySQLDatabase,
	)
}

// mustInt 把字符串配置转成 int，失败时保留 fallback，避免单个配置写错导致服务无法启动。
func mustInt(value string, fallback int) int {
	i, err := strconv.Atoi(strings.TrimSpace(value))
	if err != nil {
		return fallback
	}
	return i
}

// routes 注册所有兼容前端的 /api 路由。
// 路由尽量保持和 Spring Boot 后端一致，让前端和 Agent 不需要感知后端语言切换。
func (app *App) routes() http.Handler {
	mux := http.NewServeMux()
	api := app.cfg.APIPrefix

	// 基础健康检查。
	mux.HandleFunc("GET "+api+"/health", app.wrap(app.health))

	// 登录、注册、当前用户和退出。
	mux.HandleFunc("POST "+api+"/auth/member/login", app.wrap(app.memberLogin))
	mux.HandleFunc("POST "+api+"/auth/member/register", app.wrap(app.memberRegister))
	mux.HandleFunc("POST "+api+"/auth/admin/login", app.wrap(app.adminLogin))
	mux.HandleFunc("GET "+api+"/auth/me", app.wrap(app.requireAuth(app.currentUser)))
	mux.HandleFunc("POST "+api+"/auth/logout", app.wrap(app.logout))

	mux.HandleFunc("GET "+api+"/members/me/profile", app.wrap(app.requireAuth(app.getMyProfile)))
	mux.HandleFunc("PUT "+api+"/members/me/profile", app.wrap(app.requireAuth(app.updateMyProfile)))

	// 管理员会员管理。
	mux.HandleFunc("GET "+api+"/admin/members", app.wrap(app.requireAuth(app.requireAdmin(app.adminListMembers))))
	mux.HandleFunc("GET "+api+"/admin/members/{id}", app.wrap(app.requireAuth(app.requireAdmin(app.adminGetMember))))
	mux.HandleFunc("PUT "+api+"/admin/members/{id}", app.wrap(app.requireAuth(app.requireAdmin(app.adminUpdateMember))))
	mux.HandleFunc("POST "+api+"/admin/members/{id}/enable", app.wrap(app.requireAuth(app.requireAdmin(app.adminEnableMember))))
	mux.HandleFunc("POST "+api+"/admin/members/{id}/disable", app.wrap(app.requireAuth(app.requireAdmin(app.adminDisableMember))))

	// 商品、购物车和订单。
	mux.HandleFunc("GET "+api+"/commodities", app.wrap(app.requireAuth(app.listCommodities)))
	mux.HandleFunc("GET "+api+"/commodities/{id}", app.wrap(app.requireAuth(app.getCommodity)))
	mux.HandleFunc("GET "+api+"/admin/commodities", app.wrap(app.requireAuth(app.requireAdmin(app.adminListCommodities))))
	mux.HandleFunc("GET "+api+"/admin/commodities/{id}", app.wrap(app.requireAuth(app.requireAdmin(app.adminGetCommodity))))
	mux.HandleFunc("POST "+api+"/admin/commodities", app.wrap(app.requireAuth(app.requireAdmin(app.adminCreateCommodity))))
	mux.HandleFunc("PUT "+api+"/admin/commodities/{id}", app.wrap(app.requireAuth(app.requireAdmin(app.adminUpdateCommodity))))
	mux.HandleFunc("POST "+api+"/admin/commodities/{id}/on-sale", app.wrap(app.requireAuth(app.requireAdmin(app.adminCommodityOnSale))))
	mux.HandleFunc("POST "+api+"/admin/commodities/{id}/off-sale", app.wrap(app.requireAuth(app.requireAdmin(app.adminCommodityOffSale))))
	mux.HandleFunc("POST "+api+"/admin/commodities/{id}/stock", app.wrap(app.requireAuth(app.requireAdmin(app.adminCommodityStock))))

	mux.HandleFunc("POST "+api+"/cart/items", app.wrap(app.requireAuth(app.requireMember(app.addCartItem))))
	mux.HandleFunc("GET "+api+"/cart/items", app.wrap(app.requireAuth(app.requireMember(app.listCartItems))))
	mux.HandleFunc("PUT "+api+"/cart/items/{id}", app.wrap(app.requireAuth(app.requireMember(app.updateCartItem))))
	mux.HandleFunc("DELETE "+api+"/cart/items/{id}", app.wrap(app.requireAuth(app.requireMember(app.deleteCartItem))))

	mux.HandleFunc("POST "+api+"/orders", app.wrap(app.requireAuth(app.requireMember(app.createOrder))))
	mux.HandleFunc("GET "+api+"/orders", app.wrap(app.requireAuth(app.listOrders)))
	mux.HandleFunc("GET "+api+"/orders/{id}", app.wrap(app.requireAuth(app.getOrderDetail)))
	mux.HandleFunc("POST "+api+"/orders/{id}/cancel", app.wrap(app.requireAuth(app.requireMember(app.cancelOrder))))
	mux.HandleFunc("PUT "+api+"/orders/{id}/cancel", app.wrap(app.requireAuth(app.requireMember(app.cancelOrder))))
	mux.HandleFunc("PATCH "+api+"/orders/{id}/cancel", app.wrap(app.requireAuth(app.requireMember(app.cancelOrder))))

	// 健身房房间和会员预约。
	mux.HandleFunc("GET "+api+"/gym/rooms", app.wrap(app.requireAuth(app.listGymRooms)))
	mux.HandleFunc("GET "+api+"/gym/rooms/{id}", app.wrap(app.requireAuth(app.getGymRoom)))
	mux.HandleFunc("GET "+api+"/admin/gym/rooms", app.wrap(app.requireAuth(app.requireAdmin(app.adminListGymRooms))))
	mux.HandleFunc("GET "+api+"/admin/gym/rooms/{id}", app.wrap(app.requireAuth(app.requireAdmin(app.adminGetGymRoom))))
	mux.HandleFunc("POST "+api+"/admin/gym/rooms", app.wrap(app.requireAuth(app.requireAdmin(app.adminCreateGymRoom))))
	mux.HandleFunc("PUT "+api+"/admin/gym/rooms/{id}", app.wrap(app.requireAuth(app.requireAdmin(app.adminUpdateGymRoom))))
	mux.HandleFunc("POST "+api+"/admin/gym/rooms/{id}/enable", app.wrap(app.requireAuth(app.requireAdmin(app.adminEnableGymRoom))))
	mux.HandleFunc("POST "+api+"/admin/gym/rooms/{id}/disable", app.wrap(app.requireAuth(app.requireAdmin(app.adminDisableGymRoom))))

	mux.HandleFunc("POST "+api+"/gym/bookings", app.wrap(app.requireAuth(app.requireActiveMember(app.createGymBooking))))
	mux.HandleFunc("GET "+api+"/gym/bookings/me", app.wrap(app.requireAuth(app.requireActiveMember(app.listMyBookings))))
	mux.HandleFunc("GET "+api+"/gym/bookings", app.wrap(app.requireAuth(app.requireAdmin(app.adminListBookings))))
	mux.HandleFunc("POST "+api+"/gym/bookings/{id}/cancel", app.wrap(app.requireAuth(app.requireActiveMember(app.cancelGymBooking))))
	mux.HandleFunc("POST "+api+"/gym/bookings/{id}/admin-cancel", app.wrap(app.requireAuth(app.requireAdmin(app.adminCancelGymBooking))))

	// 课程、课程报名和后台报名管理。
	mux.HandleFunc("GET "+api+"/courses", app.wrap(app.requireAuth(app.listCourses)))
	mux.HandleFunc("POST "+api+"/courses", app.wrap(app.requireAuth(app.requireAdmin(app.adminCreateCourse))))
	mux.HandleFunc("GET "+api+"/courses/me", app.wrap(app.requireAuth(app.requireActiveMember(app.listMyCourses))))
	mux.HandleFunc("GET "+api+"/courses/enrollments", app.wrap(app.requireAuth(app.requireAdmin(app.adminListEnrollments))))
	mux.HandleFunc("POST "+api+"/courses/enrollments/{id}/cancel", app.wrap(app.requireAuth(app.requireActiveMember(app.cancelEnrollment))))
	mux.HandleFunc("POST "+api+"/courses/enrollments/{id}/admin-cancel", app.wrap(app.requireAuth(app.requireAdmin(app.adminCancelEnrollment))))
	mux.HandleFunc("GET "+api+"/courses/{id}", app.wrap(app.requireAuth(app.getCourse)))
	mux.HandleFunc("PUT "+api+"/courses/{id}", app.wrap(app.requireAuth(app.requireAdmin(app.adminUpdateCourse))))
	mux.HandleFunc("POST "+api+"/courses/{id}/enroll", app.wrap(app.requireAuth(app.requireActiveMember(app.enrollCourse))))
	mux.HandleFunc("POST "+api+"/courses/{id}/enable", app.wrap(app.requireAuth(app.requireAdmin(app.adminEnableCourse))))
	mux.HandleFunc("POST "+api+"/courses/{id}/disable", app.wrap(app.requireAuth(app.requireAdmin(app.adminDisableCourse))))

	// 后台员工管理。
	mux.HandleFunc("GET "+api+"/admin/employees", app.wrap(app.requireAuth(app.requireAdmin(app.adminListEmployees))))
	mux.HandleFunc("GET "+api+"/admin/employees/{id}", app.wrap(app.requireAuth(app.requireAdmin(app.adminGetEmployee))))
	mux.HandleFunc("POST "+api+"/admin/employees", app.wrap(app.requireAuth(app.requireAdmin(app.adminCreateEmployee))))
	mux.HandleFunc("PUT "+api+"/admin/employees/{id}", app.wrap(app.requireAuth(app.requireAdmin(app.adminUpdateEmployee))))
	mux.HandleFunc("POST "+api+"/admin/employees/{id}/enable", app.wrap(app.requireAuth(app.requireAdmin(app.adminEnableEmployee))))
	mux.HandleFunc("POST "+api+"/admin/employees/{id}/disable", app.wrap(app.requireAuth(app.requireAdmin(app.adminDisableEmployee))))

	// 后台器材管理。
	mux.HandleFunc("GET "+api+"/admin/equipments", app.wrap(app.requireAuth(app.requireAdmin(app.adminListEquipments))))
	mux.HandleFunc("GET "+api+"/admin/equipments/{id}", app.wrap(app.requireAuth(app.requireAdmin(app.adminGetEquipment))))
	mux.HandleFunc("POST "+api+"/admin/equipments", app.wrap(app.requireAuth(app.requireAdmin(app.adminCreateEquipment))))
	mux.HandleFunc("PUT "+api+"/admin/equipments/{id}", app.wrap(app.requireAuth(app.requireAdmin(app.adminUpdateEquipment))))
	mux.HandleFunc("POST "+api+"/admin/equipments/{id}/enable", app.wrap(app.requireAuth(app.requireAdmin(app.adminEnableEquipment))))
	mux.HandleFunc("POST "+api+"/admin/equipments/{id}/disable", app.wrap(app.requireAuth(app.requireAdmin(app.adminDisableEquipment))))

	// Agent 聊天接口：前端仍调 /api/chat，Go 后端转发到 Python Agent。
	mux.HandleFunc("POST "+api+"/chat", app.wrap(app.requireAuth(app.chatProxy)))

	return app.cors(app.accessLog(app.compatRoutes(mux)))
}

// compatRoutes 放置兼容旧前端/旧接口写法的路由适配逻辑。
// 当前用于支持 /api/orders/cancel/{id} 这种路径，再转到新的 cancelOrderByID。
func (app *App) compatRoutes(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		prefix := app.cfg.APIPrefix + "/orders/cancel/"
		if (r.Method == http.MethodPost || r.Method == http.MethodPut || r.Method == http.MethodPatch) &&
			strings.HasPrefix(r.URL.Path, prefix) {
			idPart := strings.Trim(strings.TrimPrefix(r.URL.Path, prefix), "/")
			id, err := strconv.ParseInt(idPart, 10, 64)
			if err != nil || id <= 0 {
				_ = writeJSON(w, http.StatusBadRequest, APIResponse{Code: 400, Message: "id must be a positive integer", Data: nil})
				return
			}
			app.wrap(app.requireAuth(app.requireMember(func(w http.ResponseWriter, r *http.Request) error {
				return app.cancelOrderByID(w, r, id)
			}))).ServeHTTP(w, r)
			return
		}
		next.ServeHTTP(w, r)
	})
}

// cors 允许 Vite 前端跨端口访问 Go 后端。
// 开发阶段 5173 -> 8080 是不同 origin，因此必须处理 OPTIONS 预检和 Authorization 头。
func (app *App) cors(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", r.Header.Get("Origin"))
		if w.Header().Get("Access-Control-Allow-Origin") == "" {
			w.Header().Set("Access-Control-Allow-Origin", "*")
		}
		w.Header().Set("Access-Control-Allow-Credentials", "true")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization, X-User-Id")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, PATCH, OPTIONS")
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		next.ServeHTTP(w, r)
	})
}

// accessLog 打印每个请求的方法、路径和耗时，方便本地调试接口是否命中 Go 后端。
func (app *App) accessLog(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next.ServeHTTP(w, r)
		log.Printf("%s %s %s", r.Method, r.URL.RequestURI(), time.Since(start).Round(time.Millisecond))
	})
}

// wrap 把项目内部 HandlerFunc 适配为标准 http.HandlerFunc。
// 这里集中捕获错误并转换成统一 APIResponse，避免每个 handler 重复写错误响应。
func (app *App) wrap(fn HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if err := fn(w, r); err != nil {
			var appErr *AppError
			if !errors.As(err, &appErr) {
				log.Printf("internal error: %+v", err)
				appErr = &AppError{Status: http.StatusInternalServerError, Code: 500, Message: "internal server error"}
			}
			writeJSON(w, appErr.Status, APIResponse{Code: appErr.Code, Message: appErr.Message, Data: nil})
		}
	}
}

// writeSuccess 返回统一成功响应。
func writeSuccess(w http.ResponseWriter, data any) error {
	return writeJSON(w, http.StatusOK, APIResponse{Code: 0, Message: "success", Data: data})
}

// writeJSON 负责真正写出 JSON，并关闭 HTML 转义，确保中文内容保持可读。
func writeJSON(w http.ResponseWriter, status int, payload any) error {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	enc := json.NewEncoder(w)
	enc.SetEscapeHTML(false)
	return enc.Encode(payload)
}

// 以下错误构造函数把常见 HTTP 状态码映射到前端可读的业务响应。
func badRequest(message string) *AppError {
	return &AppError{Status: http.StatusBadRequest, Code: 400, Message: message}
}

func unauthorized(message string) *AppError {
	if message == "" {
		message = "login required"
	}
	return &AppError{Status: http.StatusUnauthorized, Code: 401, Message: message}
}

func forbidden(message string) *AppError {
	return &AppError{Status: http.StatusForbidden, Code: 403, Message: message}
}

func notFound(message string) *AppError {
	return &AppError{Status: http.StatusNotFound, Code: 404, Message: message}
}

func serviceUnavailable(message string) *AppError {
	return &AppError{Status: http.StatusServiceUnavailable, Code: 503, Message: message}
}

// health 检查 Go 服务和 MySQL 是否可用。
func (app *App) health(w http.ResponseWriter, r *http.Request) error {
	if err := app.db.PingContext(r.Context()); err != nil {
		return serviceUnavailable("database is unavailable")
	}
	return writeSuccess(w, map[string]any{"status": "UP", "service": "go-backend"})
}

// requireAuth 校验 Authorization Bearer token，并把用户信息写入 request context。
func (app *App) requireAuth(next HandlerFunc) HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) error {
		token := resolveBearerToken(r)
		if token == "" {
			return unauthorized("login required")
		}
		user, ok := app.tokens.Get(token)
		if !ok {
			return unauthorized("login required")
		}
		ctx := context.WithValue(r.Context(), authContextKey, user)
		return next(w, r.WithContext(ctx))
	}
}

// requireMember 限制当前接口只能由会员访问。
func (app *App) requireMember(next HandlerFunc) HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) error {
		user := currentAuthUser(r)
		if user == nil {
			return unauthorized("login required")
		}
		if user.UserType != "MEMBER" {
			return forbidden("member login required")
		}
		return next(w, r)
	}
}

// requireActiveMember 限制当前接口只能由已启用会员访问。
// 注册后的 PENDING 会员可以登录，但不能预约和报名课程。
func (app *App) requireActiveMember(next HandlerFunc) HandlerFunc {
	return app.requireMember(func(w http.ResponseWriter, r *http.Request) error {
		user := currentAuthUser(r)
		if user.Status != "ACTIVE" {
			return forbidden("member account is not enabled")
		}
		return next(w, r)
	})
}

// requireAdmin 限制当前接口只能由管理员访问。
func (app *App) requireAdmin(next HandlerFunc) HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) error {
		user := currentAuthUser(r)
		if user == nil {
			return unauthorized("login required")
		}
		if user.UserType != "ADMIN" {
			return forbidden("admin login required")
		}
		return next(w, r)
	}
}

// currentAuthUser 从 request context 中取出 requireAuth 写入的用户。
func currentAuthUser(r *http.Request) *AuthUser {
	user, _ := r.Context().Value(authContextKey).(*AuthUser)
	return user
}

// resolveBearerToken 兼容 "Bearer xxx" 和直接传 token 两种 Authorization 写法。
func resolveBearerToken(r *http.Request) string {
	auth := strings.TrimSpace(r.Header.Get("Authorization"))
	if auth == "" {
		return ""
	}
	if strings.HasPrefix(strings.ToLower(auth), "bearer ") {
		return strings.TrimSpace(auth[7:])
	}
	return auth
}

// tokenEntry 是内存 token 表中的单条记录。
type tokenEntry struct {
	User      AuthUser
	ExpiresAt time.Time
}

// TokenStore 是简单的内存登录态实现。
// 注意：它不持久化到 Redis/MySQL，Go 后端重启后 token 会全部失效。
type TokenStore struct {
	mu      sync.RWMutex
	ttl     time.Duration
	entries map[string]tokenEntry
}

// NewTokenStore 创建 token 仓库。
func NewTokenStore(ttl time.Duration) *TokenStore {
	return &TokenStore{ttl: ttl, entries: make(map[string]tokenEntry)}
}

// Create 为登录用户生成随机 token，并设置过期时间。
func (s *TokenStore) Create(user AuthUser) (string, error) {
	raw := make([]byte, 24)
	if _, err := rand.Read(raw); err != nil {
		return "", err
	}
	token := "tk" + time.Now().Format("20060102150405") + hex.EncodeToString(raw)
	s.mu.Lock()
	defer s.mu.Unlock()
	s.entries[token] = tokenEntry{User: user, ExpiresAt: time.Now().Add(s.ttl)}
	return token, nil
}

// Get 读取 token 对应用户；命中后会顺延过期时间，实现简单滑动过期。
func (s *TokenStore) Get(token string) (*AuthUser, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	entry, ok := s.entries[token]
	if !ok || time.Now().After(entry.ExpiresAt) {
		delete(s.entries, token)
		return nil, false
	}
	entry.ExpiresAt = time.Now().Add(s.ttl)
	s.entries[token] = entry
	user := entry.User
	return &user, true
}

// Remove 删除 token，主要用于退出登录。
func (s *TokenStore) Remove(token string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.entries, token)
}

// decodeJSON 解析请求体为 map。
// 使用 json.Number 避免前端传来的数字被默认转成 float64 后丢失表达细节。
func decodeJSON(r *http.Request) (map[string]any, error) {
	defer r.Body.Close()
	if r.Body == http.NoBody {
		return map[string]any{}, nil
	}
	var payload map[string]any
	dec := json.NewDecoder(r.Body)
	dec.UseNumber()
	if err := dec.Decode(&payload); err != nil {
		return nil, badRequest("request body is not valid json")
	}
	return payload, nil
}

// requiredString 读取必填字符串，空值会返回 400。
func requiredString(m map[string]any, key string) (string, error) {
	value := strings.TrimSpace(asString(m[key]))
	if value == "" {
		return "", badRequest(key + " must not be blank")
	}
	return value, nil
}

// asString 把前端 JSON 中不同类型的值统一转成字符串，便于兼容表单输入。
func asString(v any) string {
	switch t := v.(type) {
	case nil:
		return ""
	case string:
		return t
	case json.Number:
		return t.String()
	case float64:
		if math.Trunc(t) == t {
			return strconv.FormatInt(int64(t), 10)
		}
		return strconv.FormatFloat(t, 'f', -1, 64)
	case bool:
		if t {
			return "true"
		}
		return "false"
	default:
		return fmt.Sprint(t)
	}
}

func nullableString(m map[string]any, key string) any {
	if _, ok := m[key]; !ok {
		return nil
	}
	value := strings.TrimSpace(asString(m[key]))
	if value == "" {
		return nil
	}
	return value
}

// asInt 读取 JSON map 中的整数值，支持 json.Number、float64 和字符串。
func asInt(m map[string]any, key string, fallback int) int {
	switch v := m[key].(type) {
	case json.Number:
		i, err := v.Int64()
		if err == nil {
			return int(i)
		}
	case float64:
		return int(v)
	case string:
		i, err := strconv.Atoi(strings.TrimSpace(v))
		if err == nil {
			return i
		}
	}
	return fallback
}

// asInt64Path 读取 Go 1.22 ServeMux 路径变量中的正整数 ID。
func asInt64Path(r *http.Request, name string) (int64, error) {
	id, err := strconv.ParseInt(r.PathValue(name), 10, 64)
	if err != nil || id <= 0 {
		return 0, badRequest(name + " must be a positive integer")
	}
	return id, nil
}

// parseDateTime 兼容前端可能提交的多种时间格式。
func parseDateTime(value string) (time.Time, error) {
	value = strings.TrimSpace(value)
	layouts := []string{
		"2006-01-02 15:04:05",
		time.RFC3339,
		"2006-01-02T15:04:05",
		"2006-01-02 15:04",
		"2006-01-02T15:04",
	}
	for _, layout := range layouts {
		if t, err := time.ParseInLocation(layout, value, time.Local); err == nil {
			return t, nil
		}
	}
	return time.Time{}, fmt.Errorf("invalid datetime: %s", value)
}

// parseDate 校验 yyyy-MM-dd 日期；空字符串会写入 nil，表示数据库 NULL。
func parseDate(value string) (any, error) {
	value = strings.TrimSpace(value)
	if value == "" {
		return nil, nil
	}
	if _, err := time.ParseInLocation("2006-01-02", value, time.Local); err != nil {
		return nil, err
	}
	return value, nil
}

// parseTimeOnly 校验房间开放时间，兼容 HH:mm 和 HH:mm:ss。
func parseTimeOnly(value string) (any, error) {
	value = strings.TrimSpace(value)
	if value == "" {
		return nil, nil
	}
	if _, err := time.Parse("15:04:05", value); err == nil {
		return value, nil
	}
	if _, err := time.Parse("15:04", value); err == nil {
		return value + ":00", nil
	}
	return nil, fmt.Errorf("invalid time: %s", value)
}

// formatDateTime 把 time.Time 转成前端更容易展示的 yyyy-MM-dd HH:mm:ss。
func formatDateTime(t time.Time) string {
	if t.IsZero() {
		return ""
	}
	return t.Format("2006-01-02 15:04:05")
}

// businessID 生成订单号、预约号、报名号等业务编号。
// prefix 用来区分 od/bk/en，后面拼接时间戳和随机字节，降低并发重复概率。
func businessID(prefix string) string {
	raw := make([]byte, 4)
	_, _ = rand.Read(raw)
	return prefix + time.Now().Format("20060102150405") + strings.ToUpper(hex.EncodeToString(raw))
}

// passwordMatches 校验密码。
// 为了兼容已有数据库，它同时支持 bcrypt 哈希和早期明文密码。
func passwordMatches(rawPassword, stored string) bool {
	if stored == "" {
		return false
	}
	if strings.HasPrefix(stored, "$2a$") || strings.HasPrefix(stored, "$2b$") || strings.HasPrefix(stored, "$2y$") {
		return bcrypt.CompareHashAndPassword([]byte(stored), []byte(rawPassword)) == nil
	}
	return stored == rawPassword
}

// bcryptHash 生成 bcrypt 密码哈希。
// 如果哈希失败，会回退到原文以避免注册流程直接中断；正常情况下不会触发。
func bcryptHash(raw string) string {
	hash, err := bcrypt.GenerateFromPassword([]byte(raw), bcrypt.DefaultCost)
	if err != nil {
		return raw
	}
	return string(hash)
}

// queryMaps 执行查询并把每一行转换成 map。
// 这样 handler 可以直接返回接近前端 VO 的结构，减少额外 DTO 定义。
func (app *App) queryMaps(ctx context.Context, query string, args ...any) ([]map[string]any, error) {
	rows, err := app.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	cols, err := rows.Columns()
	if err != nil {
		return nil, err
	}
	var result []map[string]any
	for rows.Next() {
		values := make([]any, len(cols))
		dest := make([]any, len(cols))
		for i := range values {
			dest[i] = &values[i]
		}
		if err := rows.Scan(dest...); err != nil {
			return nil, err
		}
		row := make(map[string]any, len(cols))
		for i, col := range cols {
			row[col] = normalizeDBValue(values[i])
		}
		result = append(result, row)
	}
	return result, rows.Err()
}

// normalizeDBValue 把 MySQL driver 返回的底层类型转换成 JSON 友好的类型。
func normalizeDBValue(value any) any {
	switch v := value.(type) {
	case nil:
		return nil
	case []byte:
		return string(v)
	case time.Time:
		return formatDateTime(v)
	default:
		return v
	}
}

// firstRow 从查询结果中取第一行，配合详情接口使用。
func firstRow(rows []map[string]any) (map[string]any, bool) {
	if len(rows) == 0 {
		return nil, false
	}
	return rows[0], true
}

// countRows 在事务或普通连接上执行 count 查询。
func countRows(ctx context.Context, tx queryer, query string, args ...any) (int64, error) {
	var count int64
	if err := tx.QueryRowContext(ctx, query, args...).Scan(&count); err != nil {
		return 0, err
	}
	return count, nil
}

// queryer 抽象 *sql.DB 和 *sql.Tx 的公共查询能力。
// 有了这个接口，countRows 等工具函数可以同时服务普通查询和事务查询。
type queryer interface {
	QueryRowContext(context.Context, string, ...any) *sql.Row
	ExecContext(context.Context, string, ...any) (sql.Result, error)
	QueryContext(context.Context, string, ...any) (*sql.Rows, error)
}

// memberLogin 处理会员登录。
// 成功后更新 last_login_at，并创建内存 token 返回给前端 Pinia 状态。
func (app *App) memberLogin(w http.ResponseWriter, r *http.Request) error {
	body, err := decodeJSON(r)
	if err != nil {
		return err
	}
	username, err := requiredString(body, "username")
	if err != nil {
		return err
	}
	password, err := requiredString(body, "password")
	if err != nil {
		return err
	}

	var id int64
	var passwordHash, nickname, status string
	err = app.db.QueryRowContext(
		r.Context(),
		`SELECT id, password_hash, nickname, membership_status FROM member WHERE username = ? AND deleted = 0 LIMIT 1`,
		username,
	).Scan(&id, &passwordHash, &nickname, &status)
	if errors.Is(err, sql.ErrNoRows) {
		return unauthorized("member account or password is invalid")
	}
	if err != nil {
		return err
	}
	if strings.EqualFold(status, "DISABLED") {
		return forbidden("member account is disabled")
	}
	if !passwordMatches(password, passwordHash) {
		return unauthorized("member account or password is invalid")
	}

	loginAt := time.Now()
	_, _ = app.db.ExecContext(r.Context(), `UPDATE member SET last_login_at = ? WHERE id = ?`, loginAt, id)
	user := AuthUser{UserID: id, Username: username, DisplayName: nickname, UserType: "MEMBER", Role: "MEMBER", Status: status, LoginAt: formatDateTime(loginAt)}
	token, err := app.tokens.Create(user)
	if err != nil {
		return err
	}
	return writeSuccess(w, loginVO(user, token))
}

// adminLogin 处理管理员登录。
// 它读取 admin 表，并要求管理员状态必须是 ACTIVE。
func (app *App) adminLogin(w http.ResponseWriter, r *http.Request) error {
	body, err := decodeJSON(r)
	if err != nil {
		return err
	}
	username, err := requiredString(body, "username")
	if err != nil {
		return err
	}
	password, err := requiredString(body, "password")
	if err != nil {
		return err
	}

	var id int64
	var passwordHash, name, role, status string
	err = app.db.QueryRowContext(
		r.Context(),
		`SELECT id, password_hash, name, role, status FROM admin WHERE username = ? LIMIT 1`,
		username,
	).Scan(&id, &passwordHash, &name, &role, &status)
	if errors.Is(err, sql.ErrNoRows) {
		return unauthorized("admin account or password is invalid")
	}
	if err != nil {
		return err
	}
	if !strings.EqualFold(status, "ACTIVE") {
		return forbidden("admin account is inactive")
	}
	if !passwordMatches(password, passwordHash) {
		return unauthorized("admin account or password is invalid")
	}

	loginAt := time.Now()
	_, _ = app.db.ExecContext(r.Context(), `UPDATE admin SET last_login_at = ? WHERE id = ?`, loginAt, id)
	user := AuthUser{UserID: id, Username: username, DisplayName: name, UserType: "ADMIN", Role: role, Status: status, LoginAt: formatDateTime(loginAt)}
	token, err := app.tokens.Create(user)
	if err != nil {
		return err
	}
	return writeSuccess(w, loginVO(user, token))
}

// loginVO 组装登录接口返回值，保持字段名和现有前端 store 期望一致。
func loginVO(user AuthUser, token string) map[string]any {
	return map[string]any{
		"token":       token,
		"userId":      user.UserID,
		"username":    user.Username,
		"displayName": user.DisplayName,
		"userType":    user.UserType,
		"role":        user.Role,
		"status":      user.Status,
	}
}

// memberRegister 处理会员注册。
// 新注册会员默认 PENDING：允许登录和浏览部分内容，但预约/课程报名需要管理员启用。
func (app *App) memberRegister(w http.ResponseWriter, r *http.Request) error {
	body, err := decodeJSON(r)
	if err != nil {
		return err
	}
	username, err := requiredString(body, "username")
	if err != nil {
		return err
	}
	password, err := requiredString(body, "password")
	if err != nil {
		return err
	}
	nickname, err := requiredString(body, "nickname")
	if err != nil {
		return err
	}
	phone, err := requiredString(body, "phone")
	if err != nil {
		return err
	}
	if len(password) < 6 || len(password) > 64 {
		return badRequest("password length must be between 6 and 64")
	}

	var exists int
	_ = app.db.QueryRowContext(r.Context(), `SELECT COUNT(1) FROM member WHERE username = ?`, username).Scan(&exists)
	if exists > 0 {
		return badRequest("username already exists")
	}
	_ = app.db.QueryRowContext(r.Context(), `SELECT COUNT(1) FROM member WHERE phone = ?`, phone).Scan(&exists)
	if exists > 0 {
		return badRequest("phone already exists")
	}

	res, err := app.db.ExecContext(
		r.Context(),
		`INSERT INTO member (username, password_hash, nickname, phone, email, membership_status, deleted)
		 VALUES (?, ?, ?, ?, ?, 'PENDING', 0)`,
		username,
		bcryptHash(password),
		nickname,
		phone,
		nullableString(body, "email"),
	)
	if err != nil {
		return err
	}
	id, _ := res.LastInsertId()
	return writeSuccess(w, map[string]any{
		"userId":      id,
		"username":    username,
		"displayName": nickname,
		"status":      "PENDING",
	})
}

// currentUser 返回当前登录用户的 token 内信息。
func (app *App) currentUser(w http.ResponseWriter, r *http.Request) error {
	user := currentAuthUser(r)
	return writeSuccess(w, user)
}

// logout 删除当前 Authorization token。
func (app *App) logout(w http.ResponseWriter, r *http.Request) error {
	token := resolveBearerToken(r)
	if token != "" {
		app.tokens.Remove(token)
	}
	return writeSuccess(w, nil)
}

// ensureDefaultAdmin 在空库或缺少默认账号时补一个管理员。
// 这只影响 admin001，不会覆盖已有管理员，也不会改动 Spring Boot 代码。
func (app *App) ensureDefaultAdmin() {
	var count int
	err := app.db.QueryRow(`SELECT COUNT(1) FROM admin WHERE username = 'admin001'`).Scan(&count)
	if err != nil || count > 0 {
		return
	}
	_, err = app.db.Exec(
		`INSERT INTO admin (username, password_hash, name, phone, role, status)
		 VALUES ('admin001', ?, '系统管理员', '13900000001', 'SUPER_ADMIN', 'ACTIVE')`,
		bcryptHash("123456"),
	)
	if err != nil {
		log.Printf("ensure default admin failed: %v", err)
	}
}

// chatProxy 把前端 /api/chat 请求转发给 Python Agent。
// Go 后端只负责鉴权、转发请求体和透传响应，Agent 的业务逻辑仍在 Python 服务里。
func (app *App) chatProxy(w http.ResponseWriter, r *http.Request) error {
	body, err := io.ReadAll(r.Body)
	if err != nil {
		return err
	}
	target := app.cfg.AgentBaseURL + "/chat"
	req, err := http.NewRequestWithContext(r.Context(), http.MethodPost, target, bytes.NewReader(body))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := app.client.Do(req)
	if err != nil {
		return serviceUnavailable("agent service is unavailable")
	}
	defer resp.Body.Close()
	respBody, _ := io.ReadAll(resp.Body)
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(resp.StatusCode)
	_, _ = w.Write(respBody)
	return nil
}
