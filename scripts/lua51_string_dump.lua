-- Dynamic string dumper for Luraph-like WoW AutoPlayer scripts (Lua 5.1)
-- Usage:
--   lua5.1.exe lua51_string_dump.lua <input.lua> <output.txt>

local in_path = assert(arg[1], "need input lua")
local out_path = assert(arg[2], "need output txt")

local dumped = {}
local order = {}
local function note(s)
  if type(s) ~= "string" then return end
  local n = #s
  if n < 2 or n > 2000 then return end
  if dumped[s] then return end
  local printable = 0
  for i = 1, n do
    local b = string.byte(s, i)
    if (b >= 32 and b <= 126) or b >= 128 or b == 9 or b == 10 or b == 13 then
      printable = printable + 1
    end
  end
  if printable / n < 0.70 then return end
  dumped[s] = true
  order[#order + 1] = s
end

local function note_any(v, depth, seen)
  depth = depth or 0
  seen = seen or {}
  if depth > 4 then return end
  local tv = type(v)
  if tv == "string" then
    note(v)
  elseif tv == "table" then
    if seen[v] then return end
    seen[v] = true
    local n = 0
    for k, val in pairs(v) do
      note_any(k, depth + 1, seen)
      note_any(val, depth + 1, seen)
      n = n + 1
      if n > 400 then break end
    end
  elseif tv == "function" then
    if seen[v] then return end
    seen[v] = true
    local i = 1
    while true do
      local name, val = debug.getupvalue(v, i)
      if not name then break end
      note(name)
      note_any(val, depth + 1, seen)
      i = i + 1
      if i > 200 then break end
    end
  end
end

-- Hook constructors / ops
local _char = string.char
function string.char(...)
  local r = _char(...)
  note(r)
  return r
end

local _concat = table.concat
function table.concat(t, sep, i, j)
  local r = _concat(t, sep, i, j)
  note(r)
  return r
end

local _old_loadstring = loadstring
function loadstring(src, chunkname)
  note(tostring(chunkname))
  if type(src) == "string" then
    note(src)
  end
  return _old_loadstring(src, chunkname)
end
if load then
  local _old_load = load
  function load(src, chunkname, mode, env)
    if type(src) == "string" then note(src) end
    note(tostring(chunkname))
    return _old_load(src, chunkname, mode, env)
  end
end

-- WoW mocks
local function stub() return nil end
local function stub_false() return false end
local function stub_zero() return 0 end

local frame_mt = {}
frame_mt.__index = function(self, k)
  if k == "SetScript" or k == "HookScript" or k == "RegisterEvent"
    or k == "UnregisterAllEvents" or k == "UnregisterEvent" or k == "Show" or k == "Hide"
    or k == "SetPoint" or k == "SetSize" or k == "SetWidth" or k == "SetHeight"
    or k == "SetFrameStrata" or k == "SetFrameLevel" or k == "EnableMouse"
    or k == "SetMovable" or k == "RegisterForDrag" or k == "SetClampedToScreen"
    or k == "SetBackdrop" or k == "SetBackdropColor" or k == "SetBackdropBorderColor"
    or k == "CreateTexture" or k == "CreateFontString" or k == "SetNormalTexture"
    or k == "SetText" or k == "SetOwner" or k == "AddLine" or k == "ClearLines"
    or k == "SetColorTexture" or k == "SetTexture" or k == "SetVertexColor"
    or k == "SetAlpha" or k == "SetScale" or k == "ClearAllPoints"
    or k == "SetParent" or k == "GetName" or k == "SetJustifyH" or k == "SetFontObject"
    or k == "SetAllPoints" or k == "Raise" or k == "Lower" or k == "StartMoving"
    or k == "StopMovingOrSizing" or k == "SetScript" then
    return function(obj)
      return obj or self
    end
  end
  if k == "GetScript" or k == "GetPoint" or k == "GetWidth" or k == "GetHeight" then
    return stub
  end
  return function() return self end
end

local function CreateFrame(frameType, name, parent, template)
  local f = { _type = frameType, _name = name, _parent = parent, _template = template }
  setmetatable(f, frame_mt)
  if type(name) == "string" and name ~= "" then
    _G[name] = f
  end
  return f
end

_G.CreateFrame = CreateFrame
_G.GetLocale = function() return "zhCN" end
_G.UnitName = function() return "Player" end
_G.UnitClass = function() return "WARRIOR", "Warrior" end
_G.UnitHealth = stub_zero
_G.UnitHealthMax = function() return 100 end
_G.UnitPower = stub_zero
_G.UnitPowerMax = function() return 100 end
_G.UnitExists = stub_false
_G.UnitCanAttack = stub_false
_G.UnitIsDead = stub_false
_G.UnitAffectingCombat = stub_false
_G.GetTime = function() return 123.45 end
_G.GetSpellInfo = function(id) return "Spell" .. tostring(id), nil, nil, nil, nil, nil, id end
_G.C_Spell = setmetatable({}, { __index = function() return stub end })
_G.C_UnitAuras = setmetatable({}, { __index = function() return stub end })
_G.C_Timer = {
  After = function(_, cb) if type(cb) == "function" then pcall(cb) end end,
  NewTicker = function() return { Cancel = stub } end,
}
_G.C_AddOns = { GetAddOnMetadata = function() return "1.0" end, IsAddOnLoaded = stub_false }
_G.GetAddOnMetadata = function() return "1.0" end
_G.SlashCmdList = {}
_G.DEFAULT_CHAT_FRAME = {
  AddMessage = function(_, msg) note(tostring(msg)) end,
}
_G.print = function(...)
  local t = {}
  for i = 1, select("#", ...) do
    t[#t + 1] = tostring(select(i, ...))
  end
  local s = table.concat(t, "\t")
  note(s)
end
_G.UIParent = CreateFrame("Frame", "UIParent")
_G.WorldFrame = CreateFrame("Frame", "WorldFrame")
_G.GameTooltip = CreateFrame("GameTooltip", "GameTooltip")
_G.IsAddOnLoaded = stub_false
_G.LoadAddOn = stub_false
_G.InCombatLockdown = stub_false
_G.GetBuildInfo = function() return "12.0.0", "62438", "Aug 01 2026", 120000 end
_G.WOW_PROJECT_ID = 1
_G.WOW_PROJECT_MAINLINE = 1
_G.hooksecurefunc = function() end
_G.Mixin = function(obj)
  return obj
end
_G.CopyTable = function(t)
  local r = {}
  if type(t) == "table" then
    for k, v in pairs(t) do r[k] = v end
  end
  return r
end
_G.Wipe = function(t)
  if type(t) == "table" then
    for k in pairs(t) do t[k] = nil end
  end
  return t
end

_G.LibStub = function(name)
  _G.__libs = _G.__libs or {}
  if not _G.__libs[name] then
    local lib = {}
    setmetatable(lib, {
      __index = function(self, key)
        if key == "New" or key == "NewAddon" then
          return function()
            local obj = {}
            setmetatable(obj, { __index = function() return function() end end })
            return obj
          end
        end
        return function() end
      end,
    })
    _G.__libs[name] = lib
  end
  return _G.__libs[name]
end

-- Catch unknown globals used as callables
setmetatable(_G, {
  __index = function(t, k)
    if type(k) ~= "string" then return nil end
    note(k)
    local v = function()
      return stub_false()
    end
    rawset(t, k, v)
    return v
  end,
})

local ok, err = pcall(function()
  local chunk, load_err = loadfile(in_path)
  if not chunk then
    error(load_err)
  end
  local ret = chunk()
  note_any(ret, 0, {})
  -- also scan interesting globals created during load
  for k, v in pairs(_G) do
    if type(k) == "string" and (
      k:find("Auto") or k:find("Pixel") or k:find("AP") or k:find("Hekili")
      or k:find("Skill") or k:find("Aura") or k:find("Frame")
    ) then
      note(k)
      note_any(v, 0, {})
    end
  end
end)

local fh = assert(io.open(out_path, "wb"))
fh:write("-- ok=" .. tostring(ok) .. "\n")
if not ok then
  fh:write("-- err=" .. tostring(err) .. "\n")
end
fh:write("-- count=" .. tostring(#order) .. "\n\n")
for i = 1, #order do
  fh:write(order[i])
  fh:write("\n----\n")
end
fh:close()

print(in_path, "ok=", ok, "strings=", #order, "->", out_path)
if not ok then
  print("err:", err)
end
