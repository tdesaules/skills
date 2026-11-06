package main

import (
	"fmt"
	"os"
	"syscall"
)

func main() {
	if err := syscall.Exec("/usr/bin/ruff", []string{"ruff", "check", "--no-cache", "."}, os.Environ()); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
