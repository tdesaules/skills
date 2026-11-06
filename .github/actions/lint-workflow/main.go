package main

import (
	"fmt"
	"os"
	"syscall"
)

func main() {
	args := []string{"actionlint", "-shellcheck=", "-pyflakes=", "-ignore", `^constant expression "false" in condition\.`, ".github/workflows/main.yml"}
	if err := syscall.Exec("/actionlint", args, os.Environ()); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
