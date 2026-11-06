package main

import (
	"fmt"
	"os"
	"syscall"
)

func main() {
	if err := syscall.Exec("/usr/bin/python3", []string{"python3", "-B", ".github/scripts/check_repository.py", "."}, os.Environ()); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
