-- Personal overrides loaded after Omarchy's package-owned defaults.
hl.config({
  general = { gaps_in = 3, gaps_out = 6, border_size = 2 },
  decoration = {
    rounding = 10,
    active_opacity = 1.0,
    inactive_opacity = 0.97,
    shadow = { enabled = true, range = 12, render_power = 3, color = "rgba(087f4638)" },
    blur = { enabled = true, size = 4, passes = 2 },
  },
  animations = { enabled = true },
})
hl.curve("dotfilesSmooth", { type = "bezier", points = { { 0.22, 1 }, { 0.36, 1 } } })
hl.animation({ leaf = "windows", enabled = true, speed = 3, bezier = "dotfilesSmooth", style = "slide" })
hl.animation({ leaf = "workspaces", enabled = true, speed = 4, bezier = "dotfilesSmooth", style = "slide" })

-- Keep Omarchy default hotkeys; add Super+B for the browser.
hl.unbind("SUPER + B")
o.bind("SUPER + B", "Browser", { omarchy = "browser" })
local local_path = os.getenv("HOME") .. "/.config/hypr/dotfiles-local.lua"
local file = io.open(local_path, "r")
if file then file:close(); dofile(local_path) end
