import argparse
import base64
import sys


def compact_blank_lines(source: str) -> str:
    """Keep code semantics safe: only trim trailing spaces and collapse repeated blank lines."""
    lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out = []
    last_blank = False
    for line in lines:
        s = line.rstrip()
        if s == "":
            if not last_blank:
                out.append("")
            last_blank = True
        else:
            out.append(s)
            last_blank = False
    return "\n".join(out).strip() + "\n"


def lua_long_bracket(text: str) -> str:
    # Ensure payload can always be embedded safely in Lua long-bracket string.
    eq = ""
    while f"]{eq}]" in text:
        eq += "="
    return f"[{eq}[{text}]{eq}]"


def build_base64_loader(lua_source: str) -> str:
    payload = base64.b64encode(lua_source.encode("utf-8")).decode("ascii")
    b64_literal = lua_long_bracket(payload)

    return f"""-- Obfuscated by Python Script (Base64-only, no zlib/LibCompress)
local __b64 = {b64_literal}
local __alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'

local function __decode(data)
    data = data:gsub('[^' .. __alphabet .. '=]', '')
    return (data:gsub('.', function(x)
        if x == '=' then return '' end
        local f = __alphabet:find(x, 1, true) - 1
        local r = ''
        for i = 6, 1, -1 do
            r = r .. ((f % 2 ^ i - f % 2 ^ (i - 1) > 0) and '1' or '0')
        end
        return r
    end):gsub('%d%d%d?%d?%d?%d?%d?%d?', function(x)
        if #x ~= 8 then return '' end
        local c = 0
        for i = 1, 8 do
            c = c + ((x:sub(i, i) == '1') and 2 ^ (8 - i) or 0)
        end
        return string.char(c)
    end))
end

local __src = __decode(__b64)
local __fn, __err = loadstring(__src)
if not __fn then
    error('AutoPlayer obfuscated load failed: ' .. tostring(__err))
end
__fn()
"""


def obfuscate_lua(input_file: str, output_file: str, keep_whitespace: bool) -> None:
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    if not keep_whitespace:
        content = compact_blank_lines(content)

    obfuscated_code = build_base64_loader(content)

    with open(output_file, "w", encoding="utf-8", newline="\n") as f:
        f.write(obfuscated_code)

    print(f"Obfuscation complete. Written to {output_file}")
    print("Mode: Base64 runtime loader (no zlib dependency)")


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Lua Base64 obfuscator for WoW addons")
    parser.add_argument("input", help="Input lua file")
    parser.add_argument("output", nargs="?", help="Output lua file (default: overwrite input)")
    parser.add_argument(
        "--keep-whitespace",
        action="store_true",
        help="Do not compact blank lines/trim trailing spaces before Base64 encoding.",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    in_file = args.input
    out_file = args.output if args.output else args.input
    obfuscate_lua(in_file, out_file, args.keep_whitespace)


# python Media\\obfuscator.py ConversionRuntime.lua