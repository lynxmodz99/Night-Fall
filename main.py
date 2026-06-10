"""
— Educational Purpose Only

-- Licensed and Developed by - Lynx !!

discord --> https://discord.gg/wkZgefCaPA
"""

import os
import sys
import time
import threading
import json
import struct
import socket
import ctypes
import ctypes.util
import requests
import pyfiglet
from colorama import init, Fore, Style

init(autoreset=True)

DISCORD_API = "https://discord.com/api/v9"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

GRADIENT = [
    "\033[38;2;155;0;0m",  
    "\033[38;2;175;0;0m",
    "\033[38;2;195;0;0m",
    "\033[38;2;215;0;0m",
    "\033[38;2;235;0;0m",   
    "\033[38;2;215;0;0m",
    "\033[38;2;195;0;0m",
    "\033[38;2;175;0;0m",
    "\033[38;2;155;0;0m",
]

RESET = "\033[0m"



DIM_RED = "\033[38;2;90;10;10m"
BRIGHT_RED = "\033[38;2;255;70;30m"
WHITE = "\033[38;2;235;235;235m"
DARK_BG_LINE = "\033[38;2;45;0;0m"

def gradient_text(text: str) -> str:
    out = []
    length = max(len(text) - 1, 1)

    for i, ch in enumerate(text):
        idx = int((i / length) * (len(GRADIENT) - 1))
        out.append(GRADIENT[idx] + ch)

    out.append(RESET)
    return "".join(out)

_TERROR = [
    "\033[38;2;155;0;0m",
    "\033[38;2;165;0;0m",
    "\033[38;2;175;0;0m",
    "\033[38;2;185;0;0m",
    "\033[38;2;195;0;0m",
    "\033[38;2;205;0;0m",
    "\033[38;2;215;0;0m",
    "\033[38;2;225;0;0m",
    "\033[38;2;235;0;0m",
]

def gradient_banner(text: str) -> str:
    for _font in ("banner3", "block", "colossal", "big", "slant"):
        try:
            banner = pyfiglet.figlet_format(text, font=_font, width=200)
            if banner.strip():
                break
        except Exception:
            continue
    lines = banner.rstrip("\n").split("\n")
    filled = ["".join("\u2588" if ch != " " else " " for ch in line) for line in lines]
    total = len(filled)
    painted = []
    for idx, line in enumerate(filled):
        t = idx / max(total - 1, 1)
        pos = t * (len(_TERROR) - 1)
        colour = _TERROR[round(pos)]
        painted.append(colour + line + RESET)
    return "\n".join(painted)


def separator() -> str:
    return DARK_BG_LINE + "─" * 60 + RESET


def status(msg: str, level: str = "info"):
    icons = {"info": "•", "ok": "✓", "warn": "⚠", "err": "✗", "wait": "◌"}
    colours = {
        "info": DIM_RED,
        "ok": "\033[38;2;0;200;80m",
        "warn": "\033[38;2;220;180;30m",
        "err": "\033[38;2;220;40;40m",
        "wait": DIM_RED,
    }
    icon = icons.get(level, "•")
    colour = colours.get(level, DIM_RED)
    print(f"  {colour}{icon} {msg}{RESET}")

def load_tokens() -> list[str]:

    path = os.path.join(SCRIPT_DIR, "token.txt")
    if not os.path.isfile(path):
        status("token.txt not found — create it in the script directory.", "err")
        return []
    with open(path, "r", encoding="utf-8") as f:
        tokens = [
            line.strip()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        ]
    return tokens


def validate_token(token: str) -> dict | None:
    headers = {"Authorization": token, "Content-Type": "application/json"}
    try:
        r = requests.get(f"{DISCORD_API}/users/@me", headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json()
        return None
    except requests.RequestException:
        return None

def load_messages() -> list[str]:

    path = os.path.join(SCRIPT_DIR, "msg.txt")
    if not os.path.isfile(path):
        status("msg.txt not found — create it in the script directory.", "err")
        return []
    with open(path, "r", encoding="utf-8") as f:
        msgs = [line.strip() for line in f if line.strip()]
    return msgs


def make_session(token: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({"Authorization": token, "Content-Type": "application/json"})
    return s


def send_message(session: requests.Session, channel_id: str, content: str) -> bool:
    try:
        r = session.post(
            f"{DISCORD_API}/channels/{channel_id}/messages",
            json={"content": content},
            timeout=5,
        )
        return r.status_code in (200, 201)
    except requests.RequestException:
        return False


def spam_messages(valid_tokens: list[tuple[str, dict]], channel_id: str, messages: list[str], delay: float = 0.0):

    stop_event = threading.Event()
    sent_total = 0
    lock = threading.Lock()

    def listen_for_exit():
        while not stop_event.is_set():
            try:
                user_input = input()
                if user_input.strip().lower() == "/exit":
                    stop_event.set()
                    break
            except (EOFError, KeyboardInterrupt):
                stop_event.set()
                break

    def token_worker(token: str, user: dict, worker_id: int):
        nonlocal sent_total
        session = make_session(token)
        uname = user.get("username", "?")
        idx = worker_id

        while not stop_event.is_set():
            msg = messages[idx % len(messages)]
            ok = send_message(session, channel_id, msg)

            with lock:
                sent_total += 1
                count = sent_total

            if ok:
                status(f"[{count}] {uname} → {msg[:50]}", "ok")
            else:
                status(f"[{count}] {uname} ✗ {msg[:50]}", "err")

            idx += len(valid_tokens)

            if delay > 0 and not stop_event.is_set():
                stop_event.wait(delay)

    mode_label = "SLOW" if delay > 0 else "FAST"
    print()
    status(f"Starting {mode_label} spam → channel {channel_id}", "info")
    status(f"Tokens: {len(valid_tokens)}  |  Messages loaded: {len(messages)}  |  Threads: {len(valid_tokens)}", "info")
    status("Type /exit and press Enter to stop.\n", "warn")

    exit_thread = threading.Thread(target=listen_for_exit, daemon=True)
    exit_thread.start()

    workers = []
    for i, (token, user) in enumerate(valid_tokens):
        t = threading.Thread(target=token_worker, args=(token, user, i), daemon=True)
        t.start()
        workers.append(t)

    while not stop_event.is_set():
        stop_event.wait(0.5)

    for t in workers:
        t.join(timeout=2)

    print()
    status(f"Stopped.  Total messages sent: {sent_total}", "warn")



import subprocess

FRAME_MS = 20
V_RATE = 48000
V_CH = 2
V_FRAME = int(V_RATE * FRAME_MS / 1000)
V_BYTES = V_FRAME * V_CH * 2
SILENCE = b'\xf8\xff\xfe'


def _dave_make_key_package(user_id: str):

    import struct as _s
    import nacl.signing
    import nacl.public
    def v1(b): return bytes([len(b)]) + bytes(b)
    def v2(b): return _s.pack('>H', len(b)) + bytes(b)
    def v4(b): return _s.pack('>I', len(b)) + bytes(b)

    def sign_label(sk, label: str, content: bytes) -> bytes:
        full_label = ('MLS 1.0 ' + label).encode('ascii')
        sign_content = v1(full_label) + v4(content)
        return bytes(sk.sign(sign_content).signature)

    sig_sk  = nacl.signing.SigningKey.generate()
    sig_pk  = bytes(sig_sk.verify_key)
    enc_sk  = nacl.public.PrivateKey.generate()
    enc_pk  = bytes(enc_sk.public_key)
    init_sk = nacl.public.PrivateKey.generate()
    init_pk = bytes(init_sk.public_key)

    identity   = user_id.encode('ascii')
    credential = _s.pack('>H', 1) + v2(identity)

    capabilities = (
        v1(_s.pack('>H', 1)) +
        v1(_s.pack('>H', 1)) +
        v1(b'') +
        v1(b'') +
        v1(_s.pack('>H', 1))
    )

    lifetime = _s.pack('>QQ', 0, 0x7FFFFFFFFFFFFFFF)

    leaf_body = (
        v2(enc_pk) +
        v2(sig_pk) +
        credential +
        capabilities +
        b'\x02' +
        lifetime +
        v4(b'')
    )
    leaf_sig  = sign_label(sig_sk, 'LeafNodeTBS', leaf_body)
    leaf_node = leaf_body + v2(leaf_sig)

    kp_tbs = (
        _s.pack('>H', 1) +
        _s.pack('>H', 1) +
        v2(init_pk) +
        leaf_node +
        v4(b'')
    )
    kp_sig = sign_label(sig_sk, 'KeyPackageTBS', kp_tbs)
    kp_bytes = kp_tbs + v2(kp_sig)
    return kp_bytes, bytes(init_sk)


def _dave_hkdf_extract(salt, ikm):
    import hmac as _hm, hashlib as _hl
    if not salt:
        salt = bytes(32)
    return _hm.new(salt, ikm, _hl.sha256).digest()


def _dave_hkdf_expand(prk, info, length):
    import hmac as _hm, hashlib as _hl
    t, okm, c = b'', b'', 1
    while len(okm) < length:
        t = _hm.new(prk, t + info + bytes([c]), _hl.sha256).digest()
        okm += t
        c += 1
    return okm[:length]


def _dave_hpke_decrypt(recv_priv_bytes, kem_output, ciphertext, info=b''):
    try:
        from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        return None
    KS = b'KEM\x00\x20'
    HS = b'HPKE\x00\x20\x00\x01\x00\x01'
    def lext(sid, salt, lbl, ikm):
        return _dave_hkdf_extract(salt if salt else bytes(32), b'HPKE-v1' + sid + lbl + ikm)
    def lexp(sid, prk, lbl, ctx, n):
        return _dave_hkdf_expand(prk, struct.pack('>H', n) + b'HPKE-v1' + sid + lbl + ctx, n)
    try:
        priv = X25519PrivateKey.from_private_bytes(recv_priv_bytes)
        rpk = priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        dh = priv.exchange(X25519PublicKey.from_public_bytes(kem_output))
        prk2 = lext(KS, None, b'shared_secret', dh)
        ss = lexp(KS, prk2, b'shared_secret', kem_output + rpk, 32)
        pih = lext(HS, b'', b'psk_id_hash', b'')
        ih = lext(HS, b'', b'info_hash', info)
        ksc = b'\x00' + pih + ih
        sec = lext(HS, ss, b'secret', b'')
        key = lexp(HS, sec, b'key', ksc, 16)
        nonce = lexp(HS, sec, b'base_nonce', ksc, 12)
        return AESGCM(key).decrypt(nonce, ciphertext, b'')
    except Exception:
        return None


def _dave_mls_expand_label(secret, label, ctx, n):
    lbl = b'MLS 1.0 ' + (label.encode() if isinstance(label, str) else label)
    info = struct.pack('>H', n) + bytes([len(lbl)]) + lbl + struct.pack('>I', len(ctx)) + ctx
    return _dave_hkdf_expand(secret, info, n)


def _dave_parse_welcome(welcome_data, init_sk_bytes):
    import base64 as _b64
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        return None
    try:
        if isinstance(welcome_data, str):
            wb = _b64.b64decode(welcome_data)
        elif isinstance(welcome_data, list):
            wb = bytes(welcome_data)
        else:
            wb = bytes(welcome_data)

        i = 0
        cs = struct.unpack_from('>H', wb, i)[0]; i += 2
        if cs != 1:
            return None

        sv_len = struct.unpack_from('>I', wb, i)[0]; i += 4
        sv_end = i + sv_len
        joiner_secret = None

        while i < sv_end:
            nm_len = wb[i]; i += 1 + nm_len
            ko_len = struct.unpack_from('>H', wb, i)[0]; i += 2
            ko = wb[i:i+ko_len]; i += ko_len
            ct_len = struct.unpack_from('>I', wb, i)[0]; i += 4
            ct = wb[i:i+ct_len]; i += ct_len
            if joiner_secret is None and ko_len == 32:
                try:
                    gs = _dave_hpke_decrypt(init_sk_bytes, ko, ct)
                    if gs and len(gs) >= 2:
                        js_len = gs[0]
                        if js_len > 0 and len(gs) >= 1 + js_len:
                            joiner_secret = gs[1:1+js_len]
                except Exception:
                    pass

        if not joiner_secret:
            return None

        gi_ct_len = struct.unpack_from('>I', wb, i)[0]; i += 4
        gi_ct = wb[i:i+gi_ct_len]

        js_prk = _dave_hkdf_extract(bytes(32), joiner_secret)
        wsec = _dave_mls_expand_label(js_prk, 'welcome', b'', 32)
        wkey = _dave_mls_expand_label(wsec, 'key', b'', 16)
        wnonce = _dave_mls_expand_label(wsec, 'nonce', b'', 12)
        gi = AESGCM(wkey).decrypt(wnonce, gi_ct, b'')

        p = 0
        pv = struct.unpack_from('>H', gi, p)[0]; p += 2
        gc_cs = struct.unpack_from('>H', gi, p)[0]; p += 2
        gid_l = gi[p]; p += 1
        gid = gi[p:p+gid_l]; p += gid_l
        ep = struct.unpack_from('>Q', gi, p)[0]; p += 8
        th_l = gi[p]; p += 1
        th = gi[p:p+th_l]; p += th_l
        ch_l = gi[p]; p += 1
        ch = gi[p:p+ch_l]; p += ch_l
        ex_l = struct.unpack_from('>I', gi, p)[0]; p += 4
        ex = gi[p:p+ex_l]

        gc_bytes = (
            struct.pack('>H', pv) + struct.pack('>H', gc_cs) +
            bytes([gid_l]) + gid + struct.pack('>Q', ep) +
            bytes([th_l]) + th + bytes([ch_l]) + ch +
            struct.pack('>I', ex_l) + ex
        )
        epoch_secret = _dave_hkdf_extract(bytes(32), joiner_secret)
        return epoch_secret, gc_bytes
    except Exception:
        return None


def _dave_get_media_key(epoch_secret, group_context, ssrc):
    import hashlib as _hl
    exporter_secret = _dave_mls_expand_label(epoch_secret, 'exporter', group_context, 32)
    ssrc_hash = _hl.sha256(struct.pack('>I', ssrc)).digest()
    key_material = _dave_mls_expand_label(exporter_secret, 'DAVE Media Session Key v1', ssrc_hash, 32)
    return key_material[:16]


def _dave_encrypt_opus(opus_frame, aes_key, frame_counter):
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        return opus_frame
    if not opus_frame or len(opus_frame) < 2:
        return opus_frame
    toc = opus_frame[0:1]
    payload = bytes(opus_frame[1:])
    trunc_nonce = frame_counter & 0xFFFFFFFF
    nonce = b'\x00' * 8 + struct.pack('>I', trunc_nonce)
    enc = AESGCM(aes_key).encrypt(nonce, payload, toc)
    supp_data = bytes([0]) + struct.pack('>I', 0)
    supp_len = len(supp_data)
    marker = 4 + 1 + supp_len
    appended = struct.pack('>I', trunc_nonce) + bytes([supp_len]) + supp_data + bytes([marker])
    return toc + enc + appended


def _find_ffmpeg():
    local = os.path.join(SCRIPT_DIR, 'ffmpeg.exe')
    if os.path.isfile(local):
        return local
    import shutil
    found = shutil.which('ffmpeg')
    return found  


def _load_voice_files():

    d = os.path.join(SCRIPT_DIR, "voice")
    os.makedirs(d, exist_ok=True)
    exts = ('.mp3', '.wav', '.ogg', '.flac', '.mp4', '.m4a', '.webm')
    return sorted(os.path.join(d, f) for f in os.listdir(d) if f.lower().endswith(exts))


def _decode_audio_ffmpeg(filepath, ffmpeg_path):
    cmd = [
        ffmpeg_path, '-y',
        '-i', filepath,
        '-f', 's16le',
        '-ar', str(V_RATE),
        '-ac', str(V_CH),
        '-loglevel', 'error',
        'pipe:1',
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        status(f"    ffmpeg decode error: {proc.stderr.decode(errors='replace')[:200]}", "err")
    return proc.stdout


def _parse_ogg_opus(data: bytes) -> list:
    pages = []
    i = 0
    while i + 27 <= len(data):
        if data[i:i+4] != b'OggS':
            i += 1
            continue
        num_segs = data[i + 26]
        if i + 27 + num_segs > len(data):
            break
        seg_table = list(data[i + 27: i + 27 + num_segs])
        hdr_size = 27 + num_segs
        body_size = sum(seg_table)
        if i + hdr_size + body_size > len(data):
            break
        body = data[i + hdr_size: i + hdr_size + body_size]
        pages.append((seg_table, body))
        i += hdr_size + body_size

    packets = []
    pending = bytearray()
    for page_idx, (seg_table, body) in enumerate(pages):
        if page_idx < 2:
            continue
        pos = 0
        for seg_len in seg_table:
            pending += body[pos:pos + seg_len]
            pos += seg_len
            if seg_len < 255:
                if pending:
                    packets.append(bytes(pending))
                pending = bytearray()
    if pending:
        packets.append(bytes(pending))
    return packets


def _encode_opus_frames(pcm_bytes, ffmpeg_path):
    frames = []
    total = len(pcm_bytes)
    if total == 0:
        return frames

    try:
        import opuslib
        enc = opuslib.Encoder(V_RATE, V_CH, opuslib.APPLICATION_AUDIO)
        enc.bitrate = 128000
        pos = 0
        while pos + V_BYTES <= total:
            chunk = pcm_bytes[pos:pos + V_BYTES]
            pkt = enc.encode(chunk, V_FRAME)
            if pkt and len(pkt) > 0:
                frames.append(bytes(pkt))
            pos += V_BYTES
        if frames:
            return frames
    except Exception:
        pass

    for fmt in ('ogg', 'opus'):
        cmd = [
            ffmpeg_path,
            '-f', 's16le', '-ar', str(V_RATE), '-ac', str(V_CH),
            '-i', 'pipe:0',
            '-c:a', 'libopus',
            '-b:a', '128k',
            '-vbr', 'off',
            '-frame_duration', str(FRAME_MS),
            '-application', 'audio',
            '-f', fmt,
            '-loglevel', 'error',
            'pipe:1',
        ]
        proc = subprocess.run(cmd, input=pcm_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode == 0 and proc.stdout:
            parsed = _parse_ogg_opus(proc.stdout)
            if parsed:
                return parsed
        if proc.stderr:
            status(f"    ffmpeg [{fmt}] stderr: {proc.stderr.decode(errors='replace')[:200]}", "warn")

    return frames


class _VoiceClient:

    def __init__(self, token, uid, gid, cid, stop):
        self.token, self.uid, self.gid, self.cid = token, uid, gid, cid
        self.stop = stop
        self.sid = self.vtok = self.vep = None
        self.ws = self.vws = self.udp = None
        self.key = None
        self.ssrc = self.vip = self.vport = None
        self.seq = self.ts = 0
        self._nonce = 0
        self._sn = None
        self._wl = threading.Lock()
        self._vl = threading.Lock()
        self._dead = threading.Event()
        self._init_sk = None
        self._dave_key = None
        self._dave_fc = 0

    def connect(self):

        import websocket as _W

        _HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Origin": "https://discord.com",
        }

        # ── 1. Main gateway ──
        self.ws = _W.create_connection(
            "wss://gateway.discord.gg/?v=9&encoding=json",
            timeout=20,
            header=_HEADERS,
        )
        raw = self.ws.recv()
        if not raw:
            raise RuntimeError("Gateway returned empty hello")
        hello = json.loads(raw)
        hb_iv = hello['d']['heartbeat_interval'] / 1000.0
        threading.Thread(target=self._hb, args=(hb_iv,), daemon=True).start()


        with self._wl:
            self.ws.send(json.dumps({
                "op": 2,
                "d": {
                    "token": self.token,
                    "capabilities": 16381,
                    "properties": {
                        "os": "Windows",
                        "browser": "Chrome",
                        "device": "",
                        "system_locale": "en-US",
                        "browser_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "browser_version": "120.0.0.0",
                        "os_version": "10",
                        "referrer": "https://discord.com/",
                        "referring_domain": "discord.com",
                        "release_channel": "stable",
                        "client_build_number": 270500,
                        "client_event_source": None,
                    },
                    "presence": {
                        "status": "online",
                        "since": 0,
                        "activities": [],
                        "afk": False,
                    },
                    "compress": False,
                    "client_state": {
                        "guild_versions": {},
                        "highest_last_message_id": "0",
                        "read_state_version": 0,
                        "user_guild_settings_version": -1,
                        "user_settings_version": -1,
                        "private_channels_version": "0",
                        "api_code_version": 0,
                    },
                }
            }))

        
        ready = self._eat('READY')
        if ready is None:
            raise RuntimeError("Did not receive READY from gateway (bad token?)")
        with self._wl:
            self.ws.send(json.dumps({
                "op": 4,
                "d": {
                    "guild_id": str(self.gid),
                    "channel_id": str(self.cid),
                    "self_mute": False,
                    "self_deaf": False,
                }
            }))

        
        got_state = got_server = False
        deadline = time.time() + 15  
        while not (got_state and got_server) and not self.stop.is_set():
            if time.time() > deadline:
                raise RuntimeError("Timed out waiting for VOICE_STATE_UPDATE / VOICE_SERVER_UPDATE")
            try:
                self.ws.settimeout(5)
                raw = self.ws.recv()
                if not raw:
                    raise RuntimeError("Main gateway closed while waiting for voice events")
            except Exception as e:
                if 'timed out' in str(e).lower() or 'timeout' in str(e).lower():
                    continue 
                raise RuntimeError(f"Main gateway recv error: {e}")

            m = json.loads(raw)
            op = m.get('op')
            t  = m.get('t')
            if op == 0:
                self._sn = m.get('s')
            status(f"  [gw] op={op} t={t}", "info")  

            
            if op == 9:
                raise RuntimeError("Main gateway invalidated our session (op 9) — token may be flagged")
            if op == 7:
                raise RuntimeError("Main gateway sent RECONNECT (op 7) — restarting not supported")

            if t == 'VOICE_STATE_UPDATE':
                d = m['d']
                u = d.get('user_id') or d.get('member', {}).get('user', {}).get('id')
                status(f"  [gw] VOICE_STATE_UPDATE uid={u} want={self.uid}", "info")  # debug
                if str(u) == str(self.uid):
                    self.sid = d.get('session_id')
                    status(f"  [gw] session_id = {self.sid}", "info")  # debug
                    got_state = True
            elif t == 'VOICE_SERVER_UPDATE':
                self.vtok = m['d'].get('token')
                ep = m['d'].get('endpoint', '')
                if ep:
                
                    self.vep = ep  
                status(f"  [gw] VOICE_SERVER_UPDATE endpoint={self.vep}", "info")  
                if self.vtok and self.vep:
                    got_server = True

        if not (got_state and got_server):
            raise RuntimeError("Did not receive VOICE_STATE_UPDATE + VOICE_SERVER_UPDATE")

        import ssl as _ssl
        _sslopt = {"cert_reqs": _ssl.CERT_NONE}

        if ':' in self.vep:
            vep_host, vep_port = self.vep.rsplit(':', 1)
            vws_url = f"wss://{vep_host}:{vep_port}/?v=8&encoding=json"
        else:
            vep_host = self.vep
            vws_url = f"wss://{vep_host}/?v=8&encoding=json"

        status(f"  [dbg] Connecting voice WS: {vws_url}", "info")
        self.vws = _W.create_connection(
            vws_url,
            timeout=30,
            header=_HEADERS,
            sslopt=_sslopt,
        )


        raw_v = self.vws.recv()
        if not raw_v:
            raise RuntimeError("Voice gateway returned empty hello")
        vm = json.loads(raw_v)
        status(f"  [dbg] Voice first msg op={vm.get('op')}", "info")
        if vm['op'] == 8:
            v_iv = vm['d']['heartbeat_interval'] / 1000.0
            threading.Thread(target=self._vhb, args=(v_iv,), daemon=True).start()
        else:
            raise RuntimeError(f"Expected Voice Hello (op 8), got op {vm.get('op')}")

        status(f"  [dbg] Sending Voice Identify (DAVE v1) sid={self.sid[:8]}…", "info")
        with self._vl:
            self.vws.send(json.dumps({
                "op": 0,
                "d": {
                    "server_id": str(self.gid),
                    "user_id": str(self.uid),
                    "session_id": self.sid,
                    "token": self.vtok,
                    "max_dave_protocol_version": 1,
                }
            }))

        
        import base64 as _b64
        while True:
            try:
                opcode, data = self.vws.recv_data()
            except Exception as exc:
                raise RuntimeError(f"Voice WS closed waiting for Ready: {exc}")
            if not data:
                raise RuntimeError("Voice gateway closed (no data) before Ready")
            if opcode == 8:
                import struct as _st
                code = _st.unpack('>H', data[:2])[0] if len(data) >= 2 else '?'
                msg  = data[2:].decode('utf-8', errors='replace') if len(data) > 2 else ''
                raise RuntimeError(f"Voice WS closed with code {code}: {msg}")
            vm = json.loads(data)
            op = vm.get('op')
            status(f"  [voice-ws] op={op}", "info")
            if op == 2:
                self.ssrc  = vm['d']['ssrc']
                self.vip   = vm['d']['ip']
                self.vport = vm['d']['port']
                break
            elif op == 21:
                status("  [dave] op=21 received — sending MLS KeyPackage (op 22)…", "info")
                kp, init_sk = _dave_make_key_package(str(self.uid))
                self._init_sk = init_sk
                with self._vl:
                    self.vws.send(json.dumps({
                        "op": 22,
                        "d": _b64.b64encode(kp).decode('ascii')
                    }))
                status("  [dave] op=22 sent (✓)", "ok")
            elif op == 9:
                raise RuntimeError("Voice gateway: invalid session (op 9)")
            

        
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp.settimeout(5)

        pkt = bytearray(74)
        struct.pack_into('>HHI', pkt, 0, 0x1, 70, self.ssrc)
        self.udp.sendto(bytes(pkt), (self.vip, self.vport))

        resp, _ = self.udp.recvfrom(74)
        ip_end   = resp.index(0, 8)
        our_ip   = resp[8:ip_end].decode('ascii')
        our_port = struct.unpack_from('>H', resp, 72)[0]

        
        with self._vl:
            self.vws.send(json.dumps({
                "op": 1,
                "d": {
                    "protocol": "udp",
                    "data": {
                        "address": our_ip,
                        "port": our_port,
                        "mode": "aead_xchacha20_poly1305_rtpsize"
                    }
                }
            }))



       
        while True:
            try:
                opcode, data = self.vws.recv_data()
            except Exception as exc:
                raise RuntimeError(f"Voice WS closed waiting for Session Desc: {exc}")
            if not data:
                raise RuntimeError("Voice WS closed (no data) waiting for Session Desc")
            if opcode == 8:
                import struct as _st
                code = _st.unpack('>H', data[:2])[0] if len(data) >= 2 else '?'
                msg  = data[2:].decode('utf-8', errors='replace') if len(data) > 2 else ''
                raise RuntimeError(f"Voice WS closed code {code}: {msg}")

            try:
                vm = json.loads(data)
            except Exception:
                continue
            op = vm.get('op')
            d  = vm.get('d') or {}
            status(f"  [dave] op={op} d={str(d)[:80]}", "info")

            if op == 4:
                self.key = bytes(vm['d']['secret_key'])
                status("  [dbg] Got Session Description ✔", "ok")
                break
            elif op == 20:
                tid = d.get('transition_id', 0) if isinstance(d, dict) else 0
                with self._vl:
                    self.vws.send(json.dumps({"op": 21, "d": {"transition_id": tid}}))
                if self._init_sk and isinstance(d, dict):
                    w = d.get('welcome')
                    if w:
                        ea = _dave_epoch_auth_from_welcome(w, self._init_sk)
                        if ea and self.ssrc:
                            self._dave_key = _dave_media_key(ea, self.ssrc)
                            status("  [dave] media key derived ✔", "ok")
            elif op in (11, 18, 21):
                pass

        self.udp.settimeout(None)
        threading.Thread(target=self._gw_reader, daemon=True).start()
        threading.Thread(target=self._vws_reader, daemon=True).start()

    def _eat(self, evt):
        while not self.stop.is_set():
            try:
                raw = self.ws.recv()
            except Exception:
                return None
            if not raw:
                return None
            m = json.loads(raw)
            if m.get('op') == 0:
                self._sn = m.get('s')
            if m.get('op') in (9, 7):
                raise RuntimeError(f"Gateway rejected session (op={m.get('op')})")
            if m.get('t') == evt:
                return m
        return None

    def _gw_reader(self):
        try:
            self.ws.settimeout(30)
        except Exception:
            pass
        while not self.stop.is_set() and not self._dead.is_set():
            try:
                raw = self.ws.recv()
                if not raw:
                    self._dead.set()
                    return
                m = json.loads(raw)
                op = m.get('op')
                t  = m.get('t')
                if op == 0:
                    self._sn = m.get('s')
                    if t == 'VOICE_SERVER_UPDATE':
                        self._dead.set()
                        return
                elif op == 1:
                    with self._wl:
                        self.ws.send(json.dumps({"op": 1, "d": self._sn}))
                elif op in (7, 9):
                    self._dead.set()
                    return
            except Exception as e:
                err = str(e).lower()
                if 'timed out' in err or 'timeout' in err:
                    continue
                if not self.stop.is_set():
                    self._dead.set()
                return

    def _vws_reader(self):
        import base64 as _b64
        try:
            self.vws.settimeout(30)
        except Exception:
            pass
        while not self.stop.is_set() and not self._dead.is_set():
            try:
                opcode, data = self.vws.recv_data()
                if not data:
                    self._dead.set()
                    return
                if opcode == 8:
                    self._dead.set()
                    return
                try:
                    m = json.loads(data)
                except Exception:
                    continue
                op = m.get('op')
                d  = m.get('d') or {}
                if op == 9:
                    self._dead.set()
                    return
                elif op == 4:
                    if isinstance(d, dict) and 'secret_key' in d:
                        self.key = bytes(d['secret_key'])
                elif op == 11:
                    kp, init_sk = _dave_make_key_package(str(self.uid))
                    self._init_sk = init_sk
                    with self._vl:
                        self.vws.send(json.dumps({"op": 22, "d": _b64.b64encode(kp).decode('ascii')}))
                elif op == 20:
                    tid = d.get('transition_id', 0) if isinstance(d, dict) else 0
                    with self._vl:
                        self.vws.send(json.dumps({"op": 21, "d": {"transition_id": tid}}))
                    if self._init_sk and isinstance(d, dict):
                        w = d.get('welcome')
                        if w:
                            ea = _dave_epoch_auth_from_welcome(w, self._init_sk)
                            if ea and self.ssrc:
                                self._dave_key = _dave_media_key(ea, self.ssrc)
                elif op == 21:
                    kp, init_sk = _dave_make_key_package(str(self.uid))
                    self._init_sk = init_sk
                    with self._vl:
                        self.vws.send(json.dumps({"op": 22, "d": _b64.b64encode(kp).decode('ascii')}))
            except Exception as e:
                err = str(e).lower()
                if 'timed out' in err or 'timeout' in err:
                    continue
                if not self.stop.is_set():
                    self._dead.set()
                return

    def _hb(self, interval):
        import random
        self.stop.wait(interval * random.random())
        while not self.stop.is_set() and not self._dead.is_set():
            try:
                with self._wl:
                    self.ws.send(json.dumps({"op": 1, "d": self._sn}))
            except Exception:
                self._dead.set()
                return
            self.stop.wait(interval)

    def _vhb(self, interval):
        import random
        self.stop.wait(interval * random.random())
        while not self.stop.is_set() and not self._dead.is_set():
            try:
                with self._vl:
                    self.vws.send(json.dumps({"op": 3, "d": random.randint(0, 2**31)}))
            except Exception:
                self._dead.set()
                return
            self.stop.wait(interval)

    def speak(self, on=True):
        
        try:
            with self._vl:
                self.vws.send(json.dumps({
                    "op": 5,
                    "d": {
                        "speaking": 1 if on else 0,
                        "delay": 0,
                        "ssrc": self.ssrc
                    }
                }))
        except Exception:
            pass

    def send_frame(self, opus_data):
        import nacl.bindings
        payload = opus_data
        if self._dave_key:
            payload = _dave_encrypt_opus(bytes(opus_data), self._dave_key, self._dave_fc)
            self._dave_fc += 1
        hdr = struct.pack('>BBHII', 0x80, 0x78, self.seq, self.ts, self.ssrc)
        nonce_pfx = struct.pack('<I', self._nonce)
        nonce = nonce_pfx + b'\x00' * 20
        self._nonce = (self._nonce + 1) & 0xFFFFFFFF
        encrypted = nacl.bindings.crypto_aead_xchacha20poly1305_ietf_encrypt(
            message=bytes(payload),
            aad=bytes(hdr),
            nonce=bytes(nonce),
            key=bytes(self.key),
        )
        self.udp.sendto(hdr + encrypted + nonce_pfx, (self.vip, self.vport))
        self.seq = (self.seq + 1) & 0xFFFF
        self.ts  = (self.ts  + V_FRAME) & 0xFFFFFFFF

    def close(self):
        
        try:
            with self._wl:
                self.ws.send(json.dumps({
                    "op": 4,
                    "d": {
                        "guild_id": self.gid,
                        "channel_id": None,
                        "self_mute": False,
                        "self_deaf": False
                    }
                }))
        except Exception:
            pass
        for c in (self.vws, self.ws):
            try:
                c.close()
            except Exception:
                pass
        try:
            self.udp.close()
        except Exception:
            pass


def voice_spam(valid_tokens, channel_id):
   
    try:
        import websocket
        import nacl.secret
    except ImportError as e:
        status(f"Missing package: {e.name}", "err")
        status("Run:  pip install websocket-client PyNaCl", "err")
        return

    ffmpeg_path = _find_ffmpeg()
    if not ffmpeg_path:
        status("ffmpeg not found!", "err")
        status("Put ffmpeg.exe in the script folder OR install it and add to PATH.", "err")
        status("Download: https://www.gyan.dev/ffmpeg/builds/ (ffmpeg-release-essentials.zip)", "info")
        return

    audio_files = _load_voice_files()
    if not audio_files:
        status("No audio files in voice/ folder.", "err")
        status("Add .mp3 / .wav / .ogg / .flac files to the voice/ folder.", "info")
        return

    
    tok = valid_tokens[0][0]
    try:
        r = requests.get(
            f"{DISCORD_API}/channels/{channel_id}",
            headers={"Authorization": tok},
            timeout=10,
        )
        guild_id = r.json().get("guild_id")
    except Exception:
        guild_id = None
    if not guild_id:
        status("Cannot determine guild ID from channel.", "err")
        return

   
    print()
    status("Pre-decoding audio (this runs once, shared by all tokens)…", "info")
    shared_frames = []
    for af in audio_files:
        fname = os.path.basename(af)
        status(f"  Decoding: {fname}…", "info")
        pcm = _decode_audio_ffmpeg(af, ffmpeg_path)
        if not pcm:
            status(f"  ✗ decode failed: {fname}", "err")
            continue
        status(f"  Encoding {fname} to Opus…", "info")
        frames = _encode_opus_frames(pcm, ffmpeg_path)
        if frames:
            duration = len(frames) * FRAME_MS / 1000.0
            shared_frames.append((fname, frames))
            status(f"  ✓ {fname}  ({len(frames)} frames / {duration:.1f}s)", "ok")
        else:
            status(f"  ✗ encode failed (0 frames): {fname}", "err")

    if not shared_frames:
        status("No audio could be encoded.", "err")
        return

    stop_event  = threading.Event()
    
    ready_count = [0]
    ready_lock  = threading.Lock()
    all_ready   = threading.Event()

    def listen_exit():
        while not stop_event.is_set():
            try:
                if input().strip().lower() == "/exit":
                    stop_event.set()
                    break
            except (EOFError, KeyboardInterrupt):
                stop_event.set()
                break

    def worker(tk, ud):
        uid   = ud.get("id")
        uname = ud.get("username", "?")
        while not stop_event.is_set():
            vc = None
            try:
                vc = _VoiceClient(tk, uid, guild_id, channel_id, stop_event)
                status(f"• {uname} connecting to VC…", "info")
                vc.connect()
                status(f"✓ {uname} joined VC — starting audio", "ok")
                vc.seq = 0
                vc.ts = 0
                vc._nonce = 0
                vc.speak(True)
                time.sleep(0.5)
                last_speak = time.time()
                while not stop_event.is_set() and not vc._dead.is_set():
                    for fname, frames in shared_frames:
                        if stop_event.is_set() or vc._dead.is_set():
                            break
                        status(f"  ♪ {uname} playing: {fname}", "ok")
                        t0 = time.perf_counter()
                        for i, frame in enumerate(frames):
                            if stop_event.is_set() or vc._dead.is_set():
                                break
                            try:
                                vc.send_frame(frame)
                            except Exception:
                                pass
                            target = t0 + (i + 1) * FRAME_MS / 1000.0
                            gap = target - time.perf_counter()
                            if gap > 0:
                                time.sleep(gap)
                            if time.time() - last_speak > 30:
                                vc.speak(True)
                                last_speak = time.time()
                        if not stop_event.is_set() and not vc._dead.is_set():
                            for _ in range(10):
                                try:
                                    vc.send_frame(SILENCE)
                                    time.sleep(FRAME_MS / 1000.0)
                                except Exception:
                                    break
                if vc._dead.is_set() and not stop_event.is_set():
                    raise RuntimeError("WebSocket connection dropped by Discord")
                vc.speak(False)
                vc.close()
                status(f"• {uname} left VC.", "info")
            except Exception as e:
                status(f"✗ {uname} error: {e} — reconnecting in 1s…", "err")
                if vc is not None:
                    try:
                        vc.close()
                    except Exception:
                        pass
                if not stop_event.is_set():
                    stop_event.wait(1)

    
    print()
    status(f"Voice Spam → channel {channel_id}", "info")
    status(f"Tokens: {len(valid_tokens)}  |  Audio: {len(shared_frames)} file(s)  |  ffmpeg: {os.path.basename(ffmpeg_path)}", "info")
    for fname, frames in shared_frames:
        status(f"  ▸ {fname}  ({len(frames)*FRAME_MS/1000:.1f}s)", "info")
    status("All tokens will blast simultaneously once all are connected.", "warn")
    status("Type /exit + Enter to stop.\n", "warn")

    threading.Thread(target=listen_exit, daemon=True).start()

    
    threads = []
    for i, (tk, ud) in enumerate(valid_tokens):
        t = threading.Thread(target=worker, args=(tk, ud), daemon=True)
        t.start()
        threads.append(t)
        if i < len(valid_tokens) - 1:
            time.sleep(2)

    while not stop_event.is_set():
        stop_event.wait(0.5)

    stop_event.set()
    for t in threads:
        t.join(timeout=5)

    print()
    status("Voice spam stopped.", "warn")





def clear():
    os.system("cls" if os.name == "nt" else "clear")


def draw_header():
    import re as _re
    import shutil as _sh
    clear()

    TW = _sh.get_terminal_size(fallback=(80, 24)).columns

    def centre(line: str) -> str:
        """Centre a (possibly ANSI-coloured) line in the terminal."""
        visible = _re.sub(r'\033\[[^m]*m', '', line)
        pad = max(0, (TW - len(visible)) // 2)
        return ' ' * pad + line

    _SEP_COL  = "\033[38;2;80;5;5m"
    _SUB_COL  = "\033[38;2;180;25;12m"
    _AUTH_COL = "\033[38;2;120;10;8m"
    sep_line  = _SEP_COL + '─' * min(60, TW) + RESET

    print()
    for bl in gradient_banner("Night Fall").split("\n"):
        print(centre(bl))
    print()
    print(centre(sep_line))
    print(centre(f"{_SUB_COL}Night Fall  ─  Ultimate Discord Tool{RESET}"))
    print(centre(f"{_AUTH_COL}by Lynx Modz{RESET}"))
    print(centre(sep_line))
    print()


def draw_token_status(valid_tokens: list[tuple[str, dict]]):
    if valid_tokens:
        status(f"{len(valid_tokens)} token(s) loaded & validated:", "ok")
        for token, user in valid_tokens:
            masked = token[:20] + "…" + token[-4:]
            uname = f"{user.get('username', '?')}#{user.get('discriminator', '0')}"
            print(f"      {BRIGHT_RED}▸ {WHITE}{uname}  {DIM_RED}({masked}){RESET}")
    else:
        status("No valid tokens.  Add tokens to token.txt and restart.", "err")
    print()


def main_menu(valid_tokens: list[tuple[str, dict]]):
    while True:
        draw_header()
        draw_token_status(valid_tokens)

        print(f"  {BRIGHT_RED}╔══════════════════════════════════╗{RESET}")
        print(f"  {BRIGHT_RED}║  {WHITE}[1]  Spam Messages              {BRIGHT_RED} ║{RESET}")
        print(f"  {BRIGHT_RED}║  {WHITE}[2]  Reload Tokens              {BRIGHT_RED} ║{RESET}")
        print(f"  {BRIGHT_RED}║  {WHITE}[3]  Voice Raid                 {BRIGHT_RED} ║{RESET}")
        print(f"  {BRIGHT_RED}║  {WHITE}[0]  Exit                       {BRIGHT_RED} ║{RESET}")
        print(f"  {BRIGHT_RED}╚══════════════════════════════════╝{RESET}")
        print()

        try:
            choice = input(f"  {BRIGHT_RED}▸ {WHITE}Choose an option: {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            choice = "0"

        if choice == "0":
            print()
            print(gradient_text("  Goodbye.  tnx for using ♥"))
            print()
            sys.exit(0)

        elif choice == "1":
            if not valid_tokens:
                status("No valid tokens loaded.", "err")
                input(f"\n  {DIM_RED}Press Enter to continue…{RESET}")
                continue

            messages = load_messages()
            if not messages:
                status("No messages found in msg.txt.", "err")
                input(f"\n  {DIM_RED}Press Enter to continue…{RESET}")
                continue

            status(f"Loaded {len(messages)} message(s) from msg.txt", "ok")
            status(f"Using ALL {len(valid_tokens)} token(s) in round‑robin", "info")
            print()
            try:
                channel_id = input(
                    f"  {BRIGHT_RED}▸ {WHITE}Enter channel ID to spam: {RESET}"
                ).strip()
            except (EOFError, KeyboardInterrupt):
                continue

            if not channel_id.isdigit():
                status("Invalid channel ID.", "err")
                input(f"\n  {DIM_RED}Press Enter to continue…{RESET}")
                continue

            print()
            print(f"  {BRIGHT_RED}╔══════════════════════════════════╗{RESET}")
            print(f"  {BRIGHT_RED}║  {WHITE}[1]  Fast  (no delay)          {BRIGHT_RED} ║{RESET}")
            print(f"  {BRIGHT_RED}║  {WHITE}[2]  Slow  (medium, 3s delay)  {BRIGHT_RED} ║{RESET}")
            print(f"  {BRIGHT_RED}╚══════════════════════════════════╝{RESET}")
            print()
            try:
                mode_choice = input(f"  {BRIGHT_RED}▸ {WHITE}Choose spam mode: {RESET}").strip()
            except (EOFError, KeyboardInterrupt):
                continue

            if mode_choice == "1":
                spam_delay = 0.0
            elif mode_choice == "2":
                spam_delay = 3.0
            else:
                status("Invalid mode, defaulting to Fast.", "warn")
                spam_delay = 0.0

            spam_messages(valid_tokens, channel_id, messages, spam_delay)
            input(f"\n  {DIM_RED}Press Enter to return to menu…{RESET}")

        elif choice == "2":
            valid_tokens = login_tokens()
            input(f"\n  {DIM_RED}Press Enter to continue…{RESET}")

        elif choice == "3":
            if not valid_tokens:
                status("No valid tokens loaded.", "err")
                input(f"\n  {DIM_RED}Press Enter to continue…{RESET}")
                continue

            audio_files = _load_voice_files()
            if not audio_files:
                status("No audio files in voice/ folder.", "err")
                status("Add .mp3 / .wav / .ogg / .flac files to the voice/ folder.", "info")
                input(f"\n  {DIM_RED}Press Enter to continue…{RESET}")
                continue

            status(f"Found {len(audio_files)} audio file(s) in voice/ folder", "ok")
            for af in audio_files:
                status(f"  ▸ {os.path.basename(af)}", "info")
            print()
            try:
                vc_id = input(
                    f"  {BRIGHT_RED}▸ {WHITE}Enter voice channel ID: {RESET}"
                ).strip()
            except (EOFError, KeyboardInterrupt):
                continue

            if not vc_id.isdigit():
                status("Invalid channel ID.", "err")
                input(f"\n  {DIM_RED}Press Enter to continue…{RESET}")
                continue

            voice_spam(valid_tokens, vc_id)
            input(f"\n  {DIM_RED}Press Enter to return to menu…{RESET}")

        else:
            status("Unknown option.", "warn")
            time.sleep(0.8)



def login_tokens() -> list[tuple[str, dict]]:

    raw = load_tokens()
    if not raw:
        return []

    status(f"Found {len(raw)} token(s) in token.txt — validating…", "info")
    valid: list[tuple[str, dict]] = []
    for t in raw:
        user = validate_token(t)
        if user:
            uname = f"{user.get('username', '?')}#{user.get('discriminator', '0')}"
            status(f"Valid   → {uname}", "ok")
            valid.append((t, user))
        else:
            masked = t[:15] + "…"
            status(f"Invalid → {masked}", "err")
    return valid


def main():
    draw_header()
    valid_tokens = login_tokens()
    input(f"\n  {DIM_RED}Press Enter to continue to menu…{RESET}")
    main_menu(valid_tokens)


if __name__ == "__main__":
    main()
