-- Aggressive pixel/API tracer for Luraph-like AutoPlayer Lua (Lua 5.1)
-- Logs CreateFrame/CreateTexture/SetPoint/SetSize/SetColorTexture/SetVertexColor
-- and dumps decrypted strings/upvalues more aggressively.
-- Tries to survive anti-tamper nil-arithmetic by providing arith-capable stubs.
--
-- Usage:
--   lua5.1.exe lua51_pixel_trace.lua <input.lua> <out_prefix>
-- Produces:
--   <out_prefix>_strings.txt
--   <out_prefix>_calls.txt
--   <out_prefix>_frames.txt

local in_path = assert(arg[1], "need input lua")
local out_prefix = assert(arg[2], "need output prefix")

local dumped = {}
local order = {}
local call_log = {}
local frames = {}
local MAX_CALLS = 8000
local MAX_STRINGS = 20000

local function note(s)
  if type(s) ~= "string" then return end
  local n = #s
  if n < 1 or n > 4000 then return end
  if dumped[s] then return end
  local printable = 0
  for i = 1, n do
    local b = string.byte(s, i)
    if (b >= 32 and b <= 126) or b >= 128 or b == 9 or b == 10 or b == 13 then
      printable = printable + 1
    end
  end
  if n >= 2 and printable / n < 0.55 then return end
  if #order >= MAX_STRINGS then return end
  dumped[s] = true
  order[#order + 1] = s
end

local function fmt_arg(v)
  local tv = type(v)
  if tv == "nil" then return "nil" end
  if tv == "string" then
    note(v)
    if #v > 80 then return string.format("%q", v:sub(1, 77) .. "...") end
    return string.format("%q", v)
  end
  if tv == "number" or tv == "boolean" then return tostring(v) end
  if tv == "table" then
    if v._name then return "Frame<" .. tostring(v._name) .. ">" end
    if v._tex_name then return "Tex<" .. tostring(v._tex_name) .. ">" end
    return "table"
  end
  if tv == "function" then return "function" end
  return tv
end

local function log_call(tag, obj, ...)
  if #call_log >= MAX_CALLS then return end
  local parts = { tag }
  if obj and type(obj) == "table" then
    parts[#parts + 1] = "self=" .. fmt_arg(obj)
  end
  local n = select("#", ...)
  for i = 1, n do
    parts[#parts + 1] = "a" .. i .. "=" .. fmt_arg(select(i, ...))
  end
  call_log[#call_log + 1] = table.concat(parts, " ")
end

-- Arith-capable stub: many anti-tamper paths do `local x = missing + 1`
local stub_mt = {}
local function make_stub(label)
  local t = { __stub = label or "stub" }
  setmetatable(t, stub_mt)
  return t
end

local function stub_num()
  return 0
end

stub_mt.__index = function(self, k)
  note(tostring(k))
  return make_stub(tostring(k))
end
stub_mt.__newindex = function() end
stub_mt.__call = function(self, ...)
  -- return multiple zeros to satisfy multi-ret arithmetic consumers
  return 0, 0, 0, 0, 0, 0, 0, 0
end
stub_mt.__tostring = function(self) return tostring(self.__stub or "stub") end
stub_mt.__concat = function(a, b) return tostring(a) .. tostring(b) end
stub_mt.__add = stub_num
stub_mt.__sub = stub_num
stub_mt.__mul = stub_num
stub_mt.__div = function() return 0 end
stub_mt.__mod = stub_num
stub_mt.__pow = stub_num
stub_mt.__unm = stub_num
stub_mt.__eq = function() return false end
stub_mt.__lt = function() return false end
stub_mt.__le = function() return false end
stub_mt.__len = function() return 0 end

local function note_any(v, depth, seen)
  depth = depth or 0
  seen = seen or {}
  if depth > 6 then return end
  local tv = type(v)
  if tv == "string" then
    note(v)
  elseif tv == "number" then
    -- keep small ints that may be coords/colors
    if v == math.floor(v) and v >= -10000 and v <= 10000000 then
      note(tostring(v))
    end
  elseif tv == "table" then
    if seen[v] then return end
    seen[v] = true
    local n = 0
    for k, val in pairs(v) do
      note_any(k, depth + 1, seen)
      note_any(val, depth + 1, seen)
      n = n + 1
      if n > 800 then break end
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
      if i > 400 then break end
    end
    -- also scan locals if active (usually not for dumped closures)
  end
end

-- Hook string builders
local _char = string.char
function string.char(...)
  local n = select("#", ...)
  local args = {}
  for i = 1, n do
    local v = select(i, ...)
    if type(v) ~= "number" then v = 0 end
    v = math.floor(v) % 256
    if v < 0 then v = v + 256 end
    args[i] = v
  end
  local ok, r = pcall(_char, unpack(args))
  if not ok then r = "" end
  note(r)
  return r
end

local _concat = table.concat
function table.concat(t, sep, i, j)
  if type(t) ~= "table" then return "" end
  -- VM string builders sometimes leave nil holes; sanitize a dense copy.
  -- Anti-tamper neutralization may replace nil with a stub table (truthy!), so
  -- only accept real numbers for range bounds.
  local i1 = (type(i) == "number") and i or 1
  local i2 = (type(j) == "number") and j or #t
  if type(i2) ~= "number" then i2 = 0 end
  if i2 < i1 then return "" end
  local dense = {}
  local n = 0
  for idx = i1, i2 do
    local v = t[idx]
    n = n + 1
    if v == nil then
      dense[n] = ""
    else
      dense[n] = v
    end
  end
  local ok, r = pcall(_concat, dense, sep)
  if not ok then
    -- last resort: tostring join
    r = ""
    for idx = 1, n do
      r = r .. tostring(dense[idx] or "")
      if sep and idx < n then r = r .. tostring(sep) end
    end
  end
  note(r)
  return r
end

local _format = string.format
function string.format(fmt, ...)
  local ok, r = pcall(_format, fmt, ...)
  if ok then note(r); return r end
  return tostring(fmt)
end

local _old_loadstring = loadstring
function loadstring(src, chunkname)
  note(tostring(chunkname))
  if type(src) == "string" then note(src) end
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

-- Texture / FontString method logger
local function make_region_mt(kind)
  local mt = {}
  mt.__index = function(self, k)
    note(tostring(k))
    if k == "SetColorTexture" or k == "SetTexture" or k == "SetVertexColor"
      or k == "SetAlpha" or k == "SetPoint" or k == "SetAllPoints"
      or k == "ClearAllPoints" or k == "SetSize" or k == "SetWidth" or k == "SetHeight"
      or k == "SetTexCoord" or k == "Show" or k == "Hide" or k == "SetDrawLayer"
      or k == "SetBlendMode" or k == "SetParent" or k == "SetText"
      or k == "SetTextColor" or k == "SetFontObject" or k == "SetJustifyH"
      or k == "SetSnapshot" then
      return function(obj, ...)
        log_call(kind .. "." .. k, obj, ...)
        -- record geometry/color on object
        if k == "SetPoint" then
          obj._points = obj._points or {}
          obj._points[#obj._points + 1] = { ... }
        elseif k == "SetSize" then
          obj._w, obj._h = ...
        elseif k == "SetWidth" then
          obj._w = ...
        elseif k == "SetHeight" then
          obj._h = ...
        elseif k == "SetColorTexture" or k == "SetVertexColor" then
          obj._color = { ... }
        elseif k == "SetTexture" then
          obj._texture = ...
        end
        return obj
      end
    end
    if k == "GetWidth" then return function() return self._w or 1 end end
    if k == "GetHeight" then return function() return self._h or 1 end end
    if k == "GetName" then return function() return self._name or self._tex_name end end
    if k == "IsShown" or k == "IsVisible" then return function() return true end end
    return function(obj, ...)
      log_call(kind .. "." .. tostring(k), obj, ...)
      return obj or make_stub(k)
    end
  end
  return mt
end

local tex_mt = make_region_mt("Texture")
local fs_mt = make_region_mt("FontString")

local frame_mt = {}
frame_mt.__index = function(self, k)
  note(tostring(k))
  if k == "CreateTexture" then
    return function(obj, name, layer, inherits, sublevel)
      log_call("Frame.CreateTexture", obj, name, layer, inherits, sublevel)
      local tex = {
        _tex_name = name,
        _parent = obj,
        _layer = layer,
        _kind = "texture",
      }
      setmetatable(tex, tex_mt)
      obj._textures = obj._textures or {}
      obj._textures[#obj._textures + 1] = tex
      if type(name) == "string" and name ~= "" then
        _G[name] = tex
      end
      return tex
    end
  end
  if k == "CreateFontString" then
    return function(obj, name, layer, inherits)
      log_call("Frame.CreateFontString", obj, name, layer, inherits)
      local fs = { _tex_name = name, _parent = obj, _kind = "fontstring" }
      setmetatable(fs, fs_mt)
      return fs
    end
  end
  if k == "CreateFrame" then
    return function(...) return CreateFrame(...) end
  end
  if k == "SetScript" or k == "HookScript" then
    return function(obj, event, handler)
      log_call("Frame." .. k, obj, event, type(handler))
      obj._scripts = obj._scripts or {}
      obj._scripts[event] = handler
      -- try to fire common init events once
      if type(handler) == "function" and (event == "OnLoad" or event == "OnShow" or event == "PLAYER_LOGIN" or event == "ADDON_LOADED") then
        pcall(handler, obj, "ADDON_LOADED", "AutoPlayer")
      end
      return obj
    end
  end
  if k == "RegisterEvent" then
    return function(obj, event)
      log_call("Frame.RegisterEvent", obj, event)
      obj._events = obj._events or {}
      obj._events[#obj._events + 1] = event
      return obj
    end
  end
  local logged = {
    SetPoint=true, SetSize=true, SetWidth=true, SetHeight=true,
    SetFrameStrata=true, SetFrameLevel=true, EnableMouse=true,
    SetMovable=true, RegisterForDrag=true, SetClampedToScreen=true,
    SetBackdrop=true, SetBackdropColor=true, SetBackdropBorderColor=true,
    SetNormalTexture=true, SetText=true, SetOwner=true, AddLine=true,
    ClearLines=true, SetAlpha=true, SetScale=true, ClearAllPoints=true,
    SetParent=true, Show=true, Hide=true, Raise=true, Lower=true,
    StartMoving=true, StopMovingOrSizing=true, SetAllPoints=true,
    UnregisterEvent=true, UnregisterAllEvents=true,
  }
  if logged[k] then
    return function(obj, ...)
      log_call("Frame." .. k, obj, ...)
      if k == "SetPoint" then
        obj._points = obj._points or {}
        obj._points[#obj._points + 1] = { ... }
      elseif k == "SetSize" then
        obj._w, obj._h = ...
      elseif k == "SetWidth" then
        obj._w = ...
      elseif k == "SetHeight" then
        obj._h = ...
      elseif k == "SetBackdropColor" or k == "SetBackdropBorderColor" then
        obj._bgcolor = { ... }
      end
      return obj
    end
  end
  if k == "GetName" then return function() return self._name end end
  if k == "GetWidth" then return function() return self._w or 1 end end
  if k == "GetHeight" then return function() return self._h or 1 end end
  if k == "GetScript" then return function(obj, ev) return obj._scripts and obj._scripts[ev] end end
  if k == "GetPoint" then return function() return "CENTER", nil, "CENTER", 0, 0 end end
  if k == "IsShown" or k == "IsVisible" then return function() return true end end
  return function(obj, ...)
    log_call("Frame." .. tostring(k), obj, ...)
    return obj or make_stub(k)
  end
end

function CreateFrame(frameType, name, parent, template)
  note(tostring(frameType)); note(tostring(name)); note(tostring(template))
  log_call("CreateFrame", nil, frameType, name, parent and (parent._name or "parent") or nil, template)
  local f = {
    _type = frameType,
    _name = name,
    _parent = parent,
    _template = template,
    _textures = {},
    _scripts = {},
    _events = {},
    _points = {},
  }
  setmetatable(f, frame_mt)
  frames[#frames + 1] = f
  if type(name) == "string" and name ~= "" then
    _G[name] = f
  end
  return f
end

_G.CreateFrame = CreateFrame

-- Broad WoW API stubs
local function stub_false() return false end
local function stub_zero() return 0 end
local function stub_empty() return end

local wow_funcs = {
  GetLocale=function() return "zhCN" end,
  UnitName=function() return "Player" end,
  UnitClass=function() return "WARRIOR", "Warrior" end,
  UnitHealth=stub_zero,
  UnitHealthMax=function() return 100000 end,
  UnitPower=stub_zero,
  UnitPowerMax=function() return 100 end,
  UnitExists=function(u) return u == "player" or u == "target" end,
  UnitCanAttack=stub_false,
  UnitIsDead=stub_false,
  UnitIsDeadOrGhost=stub_false,
  UnitAffectingCombat=stub_false,
  UnitIsUnit=function(a,b) return a==b end,
  UnitGUID=function(u) return "Player-0-00000000" end,
  GetTime=function() return 12345.67 end,
  GetSpellInfo=function(id) return "Spell"..tostring(id), nil, nil, nil, nil, nil, id end,
  GetSpellCooldown=function() return 0, 0, 1, 0 end,
  GetActionInfo=function() return "spell", 0 end,
  GetActionTexture=function() return "Interface\\Icons\\INV_Misc_QuestionMark" end,
  GetActionCooldown=function() return 0, 0, 1 end,
  IsUsableAction=function() return true, false end,
  IsCurrentAction=stub_false,
  GetNumGroupMembers=stub_zero,
  IsInRaid=stub_false,
  IsInGroup=stub_false,
  IsInInstance=function() return false, "none" end,
  GetInstanceInfo=function() return "World", "none", 0, "", 0, 0, false, 0, 0 end,
  GetBuildInfo=function() return "12.0.0", "62438", "Aug 01 2026", 120000 end,
  GetAddOnMetadata=function(_, field)
    if field == "Version" then return "v12.0.0.62438" end
    return "1.0"
  end,
  IsAddOnLoaded=stub_false,
  LoadAddOn=stub_false,
  InCombatLockdown=stub_false,
  hooksecurefunc=function() end,
  Mixin=function(obj) return obj end,
  CopyTable=function(t)
    local r = {}
    if type(t) == "table" then for k,v in pairs(t) do r[k]=v end end
    return r
  end,
  wipe=function(t) if type(t)=="table" then for k in pairs(t) do t[k]=nil end end return t end,
  Wipe=function(t) if type(t)=="table" then for k in pairs(t) do t[k]=nil end end return t end,
  GetCursorPosition=function() return 0, 0 end,
  GetScreenWidth=function() return 1920 end,
  GetScreenHeight=function() return 1080 end,
  GetPhysicalScreenSize=function() return 1920, 1080 end,
  GetUIScale=function() return 1 end,
  UIParentScale=function() return 1 end,
  GetCVar=function(k) note(tostring(k)); return "1" end,
  SetCVar=function(k,v) note(tostring(k)); note(tostring(v)) end,
  CreateColor=function(r,g,b,a) return {r=r,g=g,b=b,a=a or 1, GetRGB=function(s) return s.r,s.g,s.b end} end,
  GetClassColor=function() return 1, 0.8, 0, "ffffcc00" end,
}

for k,v in pairs(wow_funcs) do _G[k] = v end

_G.C_Spell = setmetatable({}, { __index = function(_, k)
  note("C_Spell." .. tostring(k))
  return function(...)
    log_call("C_Spell." .. tostring(k), nil, ...)
    return 0, 0, 0, 0
  end
end})
_G.C_UnitAuras = setmetatable({}, { __index = function(_, k)
  note("C_UnitAuras." .. tostring(k))
  return function() return nil end
end})
_G.C_Timer = {
  After = function(_, cb) if type(cb) == "function" then pcall(cb) end end,
  NewTicker = function(_, cb)
    if type(cb) == "function" then pcall(cb) end
    return { Cancel = stub_empty }
  end,
  NewTimer = function(_, cb)
    if type(cb) == "function" then pcall(cb) end
    return { Cancel = stub_empty }
  end,
}
_G.C_AddOns = {
  GetAddOnMetadata = _G.GetAddOnMetadata,
  IsAddOnLoaded = stub_false,
}
_G.SlashCmdList = {}
_G.DEFAULT_CHAT_FRAME = {
  AddMessage = function(_, msg) note(tostring(msg)); log_call("Chat.AddMessage", nil, msg) end,
}
_G.print = function(...)
  local t = {}
  for i = 1, select("#", ...) do t[#t+1] = tostring(select(i, ...)) end
  local s = table.concat(t, "\t")
  note(s)
  log_call("print", nil, s)
end
_G.UIParent = CreateFrame("Frame", "UIParent")
_G.WorldFrame = CreateFrame("Frame", "WorldFrame")
_G.GameTooltip = CreateFrame("GameTooltip", "GameTooltip")
_G.PlayerFrame = CreateFrame("Frame", "PlayerFrame")
_G.PetFrame = CreateFrame("Frame", "PetFrame")
_G.TargetFrame = CreateFrame("Frame", "TargetFrame")
_G.Minimap = CreateFrame("Frame", "Minimap")
_G.WOW_PROJECT_ID = 1
_G.WOW_PROJECT_MAINLINE = 1
_G.RAID_CLASS_COLORS = setmetatable({}, {
  __index = function() return { r=1, g=1, b=1, colorStr="ffffffff" } end
})
_G.AUTOCOMPLETE_SIMPLE = {}
_G.bit = _G.bit or {
  band=function(a,b) return 0 end, bor=function(a,b) return 0 end,
  bxor=function(a,b) return 0 end, bnot=function(a) return 0 end,
  lshift=function(a,b) return 0 end, rshift=function(a,b) return 0 end,
}

_G.LibStub = function(name, silent)
  note(tostring(name))
  _G.__libs = _G.__libs or {}
  if not _G.__libs[name] then
    local lib = {}
    setmetatable(lib, {
      __index = function(self, key)
        note(tostring(name) .. "." .. tostring(key))
        if key == "New" or key == "NewAddon" or key == "Embed" then
          return function()
            local obj = {}
            setmetatable(obj, { __index = function(_, k2)
              return function(...) log_call(tostring(name).."."..tostring(k2), nil, ...); return make_stub(k2) end
            end})
            return obj
          end
        end
        return function(...) log_call(tostring(name).."."..tostring(key), nil, ...); return make_stub(key) end
      end,
    })
    _G.__libs[name] = lib
  end
  return _G.__libs[name], true
end

-- SavedVariables placeholders
_G.AutoPlayerDB = _G.AutoPlayerDB or {}
_G.PixelPerfectUIScaleDB = _G.PixelPerfectUIScaleDB or { scale = 1 }

-- Unknown globals: prefer arith-capable table stubs. Callers that expect a
-- function still work because stub_mt.__call is defined.
setmetatable(_G, {
  __index = function(t, k)
    if type(k) ~= "string" then return nil end
    note(k)
    local v = make_stub(k)
    rawset(t, k, v)
    return v
  end,
})

-- Soft error handler: record and keep going when possible
local last_err
local function run_chunk()
  local chunk, load_err = loadfile(in_path)
  if not chunk then error(load_err) end
  local ret = chunk()
  note_any(ret, 0, {})
  -- fire any deferred OnUpdate/OnLoad scripts found on frames
  for _, f in ipairs(frames) do
    if f._scripts then
      for ev, handler in pairs(f._scripts) do
        if type(handler) == "function" then
          pcall(handler, f, "PLAYER_ENTERING_WORLD")
          pcall(handler, f, 0.016)
        end
      end
    end
    note_any(f, 0, {})
  end
  for k, v in pairs(_G) do
    if type(k) == "string" and (
      k:find("Auto") or k:find("Pixel") or k:find("AP") or k:find("Hekili")
      or k:find("Skill") or k:find("Aura") or k:find("Frame") or k:find("Color")
      or k:find("Texture") or k:find("Icon") or k:find("Macro") or k:find("Simple")
      or k:find("Position") or k:find("Light") or k:find("Spell")
    ) then
      note(k)
      note_any(v, 0, {})
    end
  end
end

-- Instruction budget + proactive nil-local neutralization (anti-tamper bypass).
-- Many Luraph-like checks leave a local nil then do `nil + n`; replacing nil
-- locals/upvalues with 0 before each line often lets decryption continue.
local INS_BUDGET = tonumber(os.getenv("LUA_TRACE_BUDGET")) or 8000000
local ins_count = 0
local function neutralize_nils(level)
  local li = 1
  while true do
    local name, val = debug.getlocal(level, li)
    if not name then break end
    if val == nil and not name:find("%*") then
      pcall(debug.setlocal, level, li, 0)
    end
    li = li + 1
    if li > 300 then break end
  end
  local info = debug.getinfo(level, "f")
  if info and info.func then
    local ui = 1
    while true do
      local name, val = debug.getupvalue(info.func, ui)
      if not name then break end
      if val == nil then
        pcall(debug.setupvalue, info.func, ui, 0)
      end
      ui = ui + 1
      if ui > 200 then break end
    end
  end
end
-- Shared neutral value: callable + arithmetic, so anti-tamper nils can be
-- used both as numbers and as functions without immediately crashing.
local NEUTRAL = make_stub("neutral")

-- count=1 is required: nil is often assigned and used within <200 opcodes.
-- Scrub several stack levels: Luraph VM nests wrapper -> dispatcher -> handler.
-- IMPORTANT: this lua5.1 build errors on getlocal(bad_level) instead of returning nil.
debug.sethook(function()
  ins_count = ins_count + 1
  if ins_count >= INS_BUDGET then
    debug.sethook()
    error("instruction_budget_exceeded:" .. tostring(ins_count), 0)
  end
  for lvl = 2, 6 do
    if not debug.getinfo(lvl, "f") then break end
    local li = 1
    while true do
      local ok, name, val = pcall(debug.getlocal, lvl, li)
      if not ok or not name then break end
      if val == nil and not name:find("%*") then
        -- Heuristic: short VM registers are usually numeric; longer names often callbacks.
        local fill = (#name <= 2) and 0 or NEUTRAL
        pcall(debug.setlocal, lvl, li, fill)
      end
      li = li + 1
      if li > 80 then break end
    end
  end
end, "", 1)

local ok, err = xpcall(run_chunk, function(e)
  last_err = e
  debug.sethook()
  -- dump current stack upvalues if possible
  for level = 2, 12 do
    local info = debug.getinfo(level, "nSf")
    if not info then break end
    note("stack:" .. tostring(info.name) .. "@" .. tostring(info.short_src) .. ":" .. tostring(info.currentline))
    if info.func then
      local i = 1
      while true do
        local name, val = debug.getupvalue(info.func, i)
        if not name then break end
        note("up:" .. tostring(name))
        note_any(val, 0, {})
        if val == nil then
          pcall(debug.setupvalue, info.func, i, NEUTRAL)
        end
        i = i + 1
        if i > 100 then break end
      end
    end
    local li = 1
    while true do
      local name, val = debug.getlocal(level, li)
      if not name then break end
      note("loc:" .. tostring(name))
      note_any(val, 0, {})
      if val == nil and not name:find("%*") then
        pcall(debug.setlocal, level, li, NEUTRAL)
      end
      li = li + 1
      if li > 200 then break end
    end
  end
  return e
end)

debug.sethook()

-- Do NOT auto-retry on arith errors: stubs can turn failures into infinite loops.
-- Budget exceed still yields partial dumps collected before the abort.

-- Write outputs
local function write_lines(path, header, lines, sep)
  local fh = assert(io.open(path, "wb"))
  fh:write(header)
  for i = 1, #lines do
    fh:write(lines[i])
    fh:write(sep or "\n")
  end
  fh:close()
end

write_lines(out_prefix .. "_strings.txt",
  "-- ok=" .. tostring(ok) .. "\n-- err=" .. tostring(err or last_err) .. "\n-- count=" .. tostring(#order) .. "\n\n",
  order, "\n----\n")

write_lines(out_prefix .. "_calls.txt",
  "-- ok=" .. tostring(ok) .. "\n-- err=" .. tostring(err or last_err) .. "\n-- calls=" .. tostring(#call_log) .. "\n\n",
  call_log, "\n")

local frame_lines = {}
for _, f in ipairs(frames) do
  frame_lines[#frame_lines + 1] = string.format(
    "FRAME name=%s type=%s w=%s h=%s points=%s textures=%s events=%s",
    tostring(rawget(f, "_name")), tostring(rawget(f, "_type")),
    tostring(rawget(f, "_w")), tostring(rawget(f, "_h")),
    tostring(f._points and #f._points or 0),
    tostring(f._textures and #f._textures or 0),
    tostring(f._events and #f._events or 0)
  )
  if f._points then
    for _, pt in ipairs(f._points) do
      local ps = {}
      for i = 1, #pt do ps[i] = fmt_arg(pt[i]) end
      frame_lines[#frame_lines + 1] = "  POINT " .. table.concat(ps, ", ")
    end
  end
  if f._textures then
    for _, tex in ipairs(f._textures) do
      local col = tex._color
      local cs = "nil"
      if col then
        local parts = {}
        for i = 1, #col do parts[i] = tostring(col[i]) end
        cs = table.concat(parts, ",")
      end
      frame_lines[#frame_lines + 1] = string.format(
        "  TEX name=%s w=%s h=%s color=%s texture=%s",
        tostring(tex._tex_name), tostring(tex._w), tostring(tex._h), cs, tostring(tex._texture)
      )
      if tex._points then
        for _, pt in ipairs(tex._points) do
          local ps = {}
          for i = 1, #pt do ps[i] = fmt_arg(pt[i]) end
          frame_lines[#frame_lines + 1] = "    TPOINT " .. table.concat(ps, ", ")
        end
      end
    end
  end
end
write_lines(out_prefix .. "_frames.txt",
  "-- frames=" .. tostring(#frames) .. "\n\n",
  frame_lines, "\n")

print(in_path, "ok=", ok, "strings=", #order, "calls=", #call_log, "frames=", #frames)
if not ok then print("err:", err or last_err) end
