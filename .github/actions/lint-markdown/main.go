package main

import (
	"fmt"
	"os"
	"syscall"
)

func main() {
	args := []string{"node", "/opt/markdownlint/node_modules/markdownlint-cli2/markdownlint-cli2-bin.mjs", "**/*.md", ".github/**/*.md", "#**/node_modules/**", "#**/*-workspace/**"}
	if err := syscall.Exec("/usr/bin/node", args, os.Environ()); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
