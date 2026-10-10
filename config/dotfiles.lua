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

local function bind(key, description, action)
  hl.unbind(key)
  o.bind(key, description, action)
end
bind("SUPER + RETURN", "Kitty", { omarchy = "terminal" })
bind("SUPER + B", "Brave Origin", { omarchy = "browser" })
bind("SUPER + C", "VS Code", { omarchy = "editor" })
bind("SUPER + E", "Files", { omarchy = "nautilus" })
bind("SUPER + Q", "Close window", hl.dsp.window.close())
bind("SUPER + M", "System monitor", "kitty -e btop")
for key, direction in pairs({ H = "l", J = "d", K = "u", L = "r" }) do
  bind("SUPER + " .. key, "Focus " .. direction, hl.dsp.focus({ direction = direction }))
  bind("SUPER + SHIFT + " .. key, "Swap " .. direction, hl.dsp.window.swap({ direction = direction }))
end
-- Native Super+Space launcher, Super+1..9 workspaces, Super+F fullscreen,
-- Super+S scratchpad, and screen capture bindings remain available.
local local_path = os.getenv("HOME") .. "/.config/hypr/dotfiles-local.lua"
local file = io.open(local_path, "r")
if file then file:close(); dofile(local_path) end
