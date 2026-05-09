// 文件作用：Go 后端启动时自动拉起前端 Vite 开发服务器。
// 用户希望“启动 Go 后端时自动启动 5173 前端”，所以这里把前端进程
// 作为 Go 后端的子进程管理；Go 后端收到退出信号时，context 会取消并停止前端进程。
package main

import (
	"bufio"
	"context"
	"errors"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// startFrontendDevServer 根据配置启动前端开发服务器。
// 默认命令是 npm run dev -- --host 0.0.0.0 --port 5173 --strictPort，
// 默认目录是 gobackend/config.yaml 中配置的 ../frontend。
func startFrontendDevServer(ctx context.Context, cfg Config) {
	if !cfg.FrontendEnabled {
		log.Println("Frontend auto-start is disabled.")
		return
	}
	if strings.TrimSpace(cfg.FrontendCommand) == "" {
		log.Println("Frontend command is empty; skip starting frontend process.")
		return
	}

	// 支持相对路径配置：从 gobackend 目录运行 go run 时，../frontend 会解析到项目的前端目录。
	workingDir := cfg.FrontendWorkingDir
	if !filepath.IsAbs(workingDir) {
		abs, err := filepath.Abs(workingDir)
		if err == nil {
			workingDir = abs
		}
	}
	info, err := os.Stat(workingDir)
	if err != nil || !info.IsDir() {
		log.Printf("Frontend working directory does not exist: %s", workingDir)
		return
	}

	// 使用 zsh -lc 执行命令，是为了兼容 npm 脚本和本机 shell 环境变量。
	// CommandContext 会在 ctx 取消时终止子进程，避免 Go 后端退出后前端残留。
	cmd := exec.CommandContext(ctx, "/bin/zsh", "-lc", cfg.FrontendCommand)
	cmd.Dir = workingDir
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		log.Printf("Failed to capture frontend stdout: %v", err)
		return
	}
	stderr, err := cmd.StderrPipe()
	if err != nil {
		log.Printf("Failed to capture frontend stderr: %v", err)
		return
	}

	if err := cmd.Start(); err != nil {
		log.Printf("Failed to start frontend process: %v", err)
		return
	}
	log.Printf("Frontend process started: %s (cwd=%s)", cfg.FrontendCommand, workingDir)

	go pumpFrontendOutput("frontend", stdout)
	go pumpFrontendOutput("frontend", stderr)

	err = cmd.Wait()
	if err != nil && !errors.Is(ctx.Err(), context.Canceled) {
		log.Printf("Frontend process exited: %v", err)
		return
	}
	log.Println("Frontend process stopped.")
}

// pumpFrontendOutput 把前端进程 stdout/stderr 接到 Go 后端日志里。
// 这样只看一个终端就能知道 Vite 是否启动成功、端口是否冲突。
func pumpFrontendOutput(prefix string, r interface{ Read([]byte) (int, error) }) {
	scanner := bufio.NewScanner(r)
	for scanner.Scan() {
		log.Printf("[%s] %s", prefix, scanner.Text())
	}
}
