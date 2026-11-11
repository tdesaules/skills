import .schema as schema

# Copy beside schema.k as config.k; adjust resources and tools to the target.
config = schema.Qemu {
    hardware = schema.Hardware {
        cpu = 2
        memory = schema.Memory {
            size = 2048
            unit = "M"
        }
        disk = schema.Disk {
            size = 32
            unit = "G"
        }
    }
    butane = schema.Butane {
        custom_pkgs = []
        custom_mise_tools = {}
    }
}
