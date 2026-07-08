#!/usr/bin/env python3
# agnos-fullscreen-test.py — end-to-end proof that cyim runs FULL-SCREEN on the
# real agnos kernel: renders on the framebuffer console (ANSI) and takes per-key
# keyboard input via kbscan#42 (src/agnos_kbd.cyr).
#
# What it does:
#   1. Stages an ext2 agnos rootfs with /bin/agnsh + /bin/cyim + /test.txt,
#      plus an ESP with gnoboot + the kernel (same layout as agnos's
#      scripts/agnsh-smoke.sh).
#   2. Boots gnoboot + OVMF + NVMe in QEMU with a USB-xHCI keyboard, so HMP
#      `sendkey` injects REAL Set-1 make/break scancodes — the exact bytes
#      kbscan#42 drains (agnsh's read#5 also fills the same kb_buf).
#   3. Waits for agnsh, reliably launches `cyim /test.txt` (retries — a dropped
#      first keystroke sends the AI-shell into intent-parsing, not exec), then
#      screendumps the framebuffer, types `i<TEXT><ESC>:wq<CR>`, screendumps
#      again, and reads /test.txt back to confirm the edit SAVED.
#
# PASS iff the file gained <TEXT> at the head of line 1. Screendumps land in the
# work dir (A.ppm = launched, B.ppm = after edit) for eyeballing the render.
#
# Prereqs (built first; override paths via env):
#   AGNOS_ROOT   agnos repo   (kernel: $AGNOS_ROOT/build/agnos — ./scripts/build.sh)
#   GNOBOOT      $GNOBOOT_ROOT/build/BOOTX64.EFI
#   AGNSH_BIN    agnoshi build/agnsh_agnos   (cyrius build --agnos src/agnsh.cyr ...)
#   CYIM_BIN     this repo's build/cyim_agnos (cyrius build --agnos src/main.cyr ...)
# Host tools: qemu-system-x86_64, parted, sgdisk, mformat/mmd/mcopy (mtools),
#             mkfs.ext2, dd, debugfs, OVMF.
#
# Usage:  python3 scripts/agnos-fullscreen-test.py [WORKDIR]
import os, socket, subprocess, sys, time

HOME = os.path.expanduser("~")
def repo(env, default): return os.environ.get(env, default)
AGNOS   = repo("AGNOS_ROOT", f"{HOME}/Repos/agnos")
GNOBOOT = repo("GNOBOOT",    f"{HOME}/Repos/gnoboot/build/BOOTX64.EFI")
KERNEL  = repo("KERNEL",     f"{AGNOS}/build/agnos")
AGNSH   = repo("AGNSH_BIN",  f"{HOME}/Repos/agnoshi/build/agnsh_agnos")
HERE    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CYIM    = repo("CYIM_BIN",   f"{HERE}/build/cyim_agnos")
WORK    = sys.argv[1] if len(sys.argv) > 1 else "/tmp/cyim-agnos-fs-test"
MON     = "/tmp/cyim-agnos-fs.sock"
TEXT    = "ZED"                                    # inserted at head of line 1
FIRST   = "alpha line one"                         # original line 1

def die(msg): print("FAIL:", msg); sys.exit(1)
def sh(cmd): subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def find_ovmf():
    code = vars_ = ""
    for c in ("/usr/share/edk2/x64/OVMF_CODE.4m.fd", "/usr/share/edk2/x64/OVMF_CODE.fd",
              "/usr/share/OVMF/OVMF_CODE.fd", "/usr/share/OVMF/OVMF_CODE_4M.fd"):
        if os.path.exists(c): code = c; break
    for v in ("/usr/share/edk2/x64/OVMF_VARS.4m.fd", "/usr/share/edk2/x64/OVMF_VARS.fd",
              "/usr/share/OVMF/OVMF_VARS.fd", "/usr/share/OVMF/OVMF_VARS_4M.fd"):
        if os.path.exists(v): vars_ = v; break
    if not code or not vars_: die("OVMF firmware not found")
    return code, vars_

def stage(img):
    for f in (GNOBOOT, KERNEL, AGNSH, CYIM):
        if not os.path.exists(f): die(f"missing prereq {f}")
    seed = os.path.join(WORK, "seed"); os.makedirs(os.path.join(seed, "bin"), exist_ok=True)
    sh(["cp", AGNSH, os.path.join(seed, "bin/agnsh")])
    sh(["cp", CYIM,  os.path.join(seed, "bin/cyim")])
    open(os.path.join(seed, "test.txt"), "w").write(
        FIRST + "\nbeta line two\ngamma line three\ndelta line four\n")
    off = 33 * 1048576; blocks = (67 * 1048576) // 4096
    feat = "^resize_inode,^dir_index,^metadata_csum,^64bit,^uninit_bg"
    sh(["dd", "if=/dev/zero", f"of={img}", "bs=1M", "count=128", "status=none"])
    sh(["parted", "-s", img, "mklabel", "gpt",
        "mkpart", "ESP", "fat32", "1MiB", "33MiB", "set", "1", "esp", "on",
        "mkpart", "agnos-fs", "ext2", "33MiB", "100MiB"])
    sh(["sgdisk", "-t", "2:8300", img])
    sh(["mformat", "-i", f"{img}@@1048576", "-F"])
    sh(["mmd", "-i", f"{img}@@1048576", "::EFI", "::EFI/BOOT", "::boot"])
    sh(["mcopy", "-i", f"{img}@@1048576", GNOBOOT, "::EFI/BOOT/BOOTX64.EFI"])
    sh(["mcopy", "-i", f"{img}@@1048576", KERNEL, "::boot/agnos"])
    sh(["mkfs.ext2", "-F", "-q", "-L", "AGNOS-CYIM", "-b", "4096", "-m", "0",
        "-O", feat, "-d", seed, "-E", f"offset={off}", img, str(blocks)])

def main():
    os.makedirs(WORK, exist_ok=True)
    img = os.path.join(WORK, "agnos.img"); ser = os.path.join(WORK, "serial.log")
    code, vars_src = find_ovmf(); varfd = os.path.join(WORK, "vars.fd")
    print("[1/4] staging ext2 rootfs (/bin/agnsh + /bin/cyim + /test.txt)...")
    stage(img); sh(["cp", vars_src, varfd])
    open(ser, "w").close()
    try: os.unlink(MON)
    except FileNotFoundError: pass

    print("[2/4] booting QEMU (gnoboot + OVMF + NVMe + USB keyboard)...")
    qemu = subprocess.Popen([
        "qemu-system-x86_64", "-machine", "q35", "-m", "512M", "-cpu", "max",
        "-drive", f"if=pflash,format=raw,readonly=on,file={code}",
        "-drive", f"if=pflash,format=raw,file={varfd}",
        "-drive", f"file={img},format=raw,if=none,id=disk0",
        "-device", "nvme,drive=disk0,serial=AGNOS-CYIM",
        "-device", "qemu-xhci,id=xhci", "-device", "usb-kbd,bus=xhci.0",
        "-serial", f"file:{ser}", "-display", "none", "-no-reboot",
        "-monitor", f"unix:{MON},server,nowait",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def read_ser():
        try: return open(ser, "rb").read().decode("latin1")
        except OSError: return ""
    def wait_for(sub, timeout, since=0):
        t0 = time.time()
        while time.time() - t0 < timeout:
            if sub in read_ser()[since:]: return True
            if qemu.poll() is not None: return False
            time.sleep(0.3)
        return False

    KM = {" ": "spc", "/": "slash", ".": "dot", "\n": "ret", ":": "shift-semicolon"}
    mon = [None]
    def hmp(cmd):
        mon[0].sendall((cmd + "\n").encode()); time.sleep(0.05)
        try: mon[0].recv(4096)
        except Exception: pass
    def key(k, dwell=0.12): hmp("sendkey " + k); time.sleep(dwell)
    def keyname(ch):
        if ch in KM: return KM[ch]
        return "shift-" + ch.lower() if ch.isalpha() and ch.isupper() else ch
    def typ(s, per=0.14):
        for ch in s: key(keyname(ch), per)

    rc = 1
    try:
        if not wait_for("exec /bin/agnsh", 60): die("agnsh never exec'd (kernel/agnsh boot failure)")
        time.sleep(3.0)
        mon[0] = socket.socket(socket.AF_UNIX); mon[0].connect(MON); mon[0].settimeout(2)
        try: mon[0].recv(4096)
        except Exception: pass

        print("[3/4] launching cyim + driving edit via sendkey...")
        launched = False
        for attempt in range(4):
            base = len(read_ser())
            key("ret", 0.5)                       # prime (absorb the first-key drop)
            typ("cyim /test.txt\n")
            if wait_for("NORMAL", 8, since=base):  # cyim's modeline hits the serial-mirrored console
                launched = True; break
            print(f"      launch attempt {attempt+1} missed; retrying")
        if not launched: die("cyim never rendered (launch keystrokes not landing)")
        time.sleep(1.2); hmp(f"screendump {WORK}/A.ppm"); time.sleep(0.6)
        typ(f"i{TEXT}"); key("esc", 0.5)          # insert TEXT at start of line 1, back to NORMAL
        time.sleep(1.0); hmp(f"screendump {WORK}/B.ppm"); time.sleep(0.6)
        typ(":wq\n"); time.sleep(4.0)             # save + quit
    finally:
        try: qemu.terminate(); qemu.wait(timeout=5)
        except Exception:
            try: qemu.kill()
            except Exception: pass

    print("[4/4] verifying the saved file...")
    part = os.path.join(WORK, "part.ext2")
    sh(["dd", f"if={img}", f"of={part}", "bs=1M", "skip=33", "count=67", "status=none"])
    out = subprocess.run(["debugfs", "-R", "cat /test.txt", part],
                         capture_output=True, text=True).stdout
    line1 = out.splitlines()[0] if out.splitlines() else ""
    print("      /test.txt line 1:", repr(line1))
    if line1 == TEXT + FIRST:
        print(f"PASS — cyim full-screen on agnos: keyboard-typed {TEXT!r} inserted + saved.")
        print(f"       screendumps: {WORK}/A.ppm (launched) {WORK}/B.ppm (edited)")
        return 0
    die(f"edit did not save (expected {TEXT+FIRST!r}, got {line1!r})")

if __name__ == "__main__":
    sys.exit(main())
