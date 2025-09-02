def load_config(filename="config.json"):
    config = {}
    with open(filename) as f:
        for line in f:
            line = line.strip().strip(",")
            if not line or line[0] in "{}":
                continue
            key, val = line.split(":", 1)
            key = key.strip().strip('"')
            val = val.strip().strip('"')
            config[key] = val
    return config

def save_config(config, filename="config.json"):
    with open(filename, "w") as f:
        f.write("{\n")
        items = list(config.items())
        for i, (k, v) in enumerate(items):
            f.write(f'  "{k}": ')
            if k in ("server_ip", "filename"):   # keep strings quoted
                f.write(f'"{v}"')
            else:
                f.write(v)
            if i < len(items)-1:
                f.write(",")
            f.write("\n")
        f.write("}\n")

def modify_config(key, value, filename="config.json"):
    config = load_config(filename)
    config[key] = str(value)
    save_config(config, filename)
