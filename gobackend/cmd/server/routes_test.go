// 文件作用：Go 后端路由注册的最小回归测试。
// Go 1.22 ServeMux 在遇到冲突路由时会 panic，本测试用于尽早发现
// 新增接口时是否和已有 /api 路径、HTTP 方法或路径变量产生冲突。
package main

import "testing"

// TestRoutesRegister 只验证 routes() 能完整构建出 handler。
// 这里不连接 MySQL，也不启动真实 HTTP 服务，因此适合作为快速冒烟测试。
func TestRoutesRegister(t *testing.T) {
	app := &App{
		cfg: Config{
			APIPrefix:           "/api",
			AgentBaseURL:        "http://localhost:8000",
			AgentRequestTimeout: 10,
			AuthTokenTTL:        10,
		},
		tokens: NewTokenStore(10),
	}

	if app.routes() == nil {
		t.Fatal("routes returned nil handler")
	}
}
