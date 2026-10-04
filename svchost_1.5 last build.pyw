import os
import sys
import time
import re
import json
import random
import threading
import subprocess
import tempfile
import ctypes
from typing import Optional, List, Tuple

import requests
import pyperclip
import keyboard
import tkinter as tk
from tkinter import ttk, messagebox

CONFIG = {
    "ACTIVE_PRESET": "openrouter",
    "ACTIVE_THEME": "sky_azure",
    "GLOW_MODE": "soft",
    "GLASS_BLUR": True,
    "GLASS_OPACITY": 0.94,
    "SYNC_PIXEL_THEME": False,
    
    "API_URL": "https://openrouter.ai/api/v1/chat/completions",
    "API_KEY": "",
    "MODEL": "nvidia/nemotron-3-ultra-550b-a55b:free",
    "TEMPERATURE": 0.15,

    "API_KEYS": {
        "groq": "",
        "openrouter": "",
        "together": "",
        "cerebras": "",
        "gemini": "",
        "deepseek": "",
        "openai": "",
    },

    "MODELS": {
        "groq": "qwen/qwen3.8-27b",
        "openrouter": "nvidia/nemotron-3-ultra-550b-a55b:free",
        "together": "Prism-ML/Ternary-Bonsai-27B",
        "cerebras": "llama3.3-70b",
        "gemini": "gemini-3.5-flash-lite",
        "deepseek": "deepseek-chat",
        "openai": "gpt-4o-mini",
    },

    "HOTKEYS": {
        "send": "ctrl+left shift+f1",
        "magic_print": "ctrl+left shift+f2",
        "quick_insert": "ctrl+left shift+f3",
        "clear_code": "ctrl+left shift+f4",
        "add_context": "ctrl+left shift+f5",
        "clear_context": "ctrl+left shift+f6",
        "retry": "ctrl+left shift+f7",
        "menu": "ctrl+left shift+f8",
        "panic_sleep": "ctrl+left shift+f9",
        "panic_kill": "ctrl+left shift+f12",
        "panic_kill_alt": "ctrl+left shift+delete"
    },

    "COLORS": {
        "idle": "#05131a",
        "loading": "#2dd4bf",
        "ready": "#4ade80",
        "orange": "#fb923c",
        "red": "#f87171",
        "error": "#f87171",
        "bar_active": "#0f766e",
    },

    "STATUS_PIXEL_SIZE": "2x2",
    "STATUS_PIXEL_POS": "+0+0",
    "BAR_PIXELS_COUNT": 5,
    "LOG_LIMIT": 15000,
    "MAGIC_CHUNK_SIZE": 1,
    "MAGIC_PRINT": {
        "mode": "simulation",
        "key_delay_min": 0.14,
        "key_delay_max": 0.26,
        "error_probability": 1.0,
        "typo_hold_min": 0.2,
        "typo_hold_max": 0.45,
        "erase_delay_min": 0.1,
        "erase_delay_max": 0.24,
        "correction_delay_min": 0.16,
        "correction_delay_max": 0.38,
        "space_delay_min": 0.14,
        "space_delay_max": 0.32,
        "punctuation_delay_min": 0.25,
        "punctuation_delay_max": 0.55,
        "newline_delay_min": 0.3,
        "newline_delay_max": 0.7,
        "word_pause_probability": 22.0,
        "word_pause_min": 0.35,
        "word_pause_max": 0.9,
        "thinking_probability": 14.0,
        "thinking_pause_min": 1.2,
        "thinking_pause_max": 3.0,
        "skip_auto_indent": True,
    },
}

CELESTIAL_THEMES = {
    "sky_azure": {
        "label": "🌌 Лазурный Небосвод (Azure Glass)",
        "type": "Акриловое стекло & Неон",
        "desc": "Глубокая ночная синева с полупрозрачным матовым стеклом и небесной лазурью",
        "bg_main": "#070e18",
        "bg_header": "#0c182b",
        "bg_card": "#101f35",
        "bg_entry": "#162844",
        "accent_primary": "#38bdf8",
        "accent_secondary": "#0284c7",
        "accent_glow": "#0ea5e9",
        "border_color": "#1e3a5f",
        "border_glow": "#38bdf8",
        "text_main": "#f0f9ff",
        "text_muted": "#7dd3fc",
        "text_dim": "#64748b",
        "button_bg": "#0284c7",
        "button_hover": "#0369a1",
        "success": "#34d399",
        "error": "#fb7185",
        "bar_active": "#0284c7",
        "glass_tint": "#070e18",
        "glass_alpha": 220,
    },
    "sky_aurora": {
        "label": "❄️Северная Аврора (Polar Aurora Glass)",
        "type": "Акриловое стекло & Неон",
        "desc": "Мягкий полярный сумрак и изумрудно-бирюзовые всполохи сквозь матовое стекло",
        "bg_main": "#05131a",
        "bg_header": "#09222c",
        "bg_card": "#0d2c3a",
        "bg_entry": "#133b4d",
        "accent_primary": "#2dd4bf",
        "accent_secondary": "#0d9488",
        "accent_glow": "#14b8a6",
        "border_color": "#164e63",
        "border_glow": "#2dd4bf",
        "text_main": "#f0fdfa",
        "text_muted": "#5eead4",
        "text_dim": "#52636a",
        "button_bg": "#0f766e",
        "button_hover": "#115e59",
        "success": "#4ade80",
        "error": "#f43f5e",
        "bar_active": "#0f766e",
        "glass_tint": "#05131a",
        "glass_alpha": 218,
    },
    "sky_lunar": {
        "label": "🌙 Лунная Дымка (Lunar Mist Glass)",
        "type": "Акриловое стекло & Неон",
        "desc": "Холодный стальной индиго, дымчатое матовое стекло и серебристо-лунный свет",
        "bg_main": "#0a0f1d",
        "bg_header": "#12192f",
        "bg_card": "#17223e",
        "bg_entry": "#1e2c50",
        "accent_primary": "#93c5fd",
        "accent_secondary": "#3b82f6",
        "accent_glow": "#60a5fa",
        "border_color": "#233876",
        "border_glow": "#93c5fd",
        "text_main": "#f8fafc",
        "text_muted": "#bfdbfe",
        "text_dim": "#64748b",
        "button_bg": "#2563eb",
        "button_hover": "#1d4ed8",
        "success": "#38ef7d",
        "error": "#f87171",
        "bar_active": "#2563eb",
        "glass_tint": "#0a0f1d",
        "glass_alpha": 222,
    },
    "sky_horizon": {
        "label": "🌅 Небесный Горизонт (Cyan ➜ Indigo)",
        "type": "Градиентный Glass-стиль",
        "desc": "Переход от бирюзового неба к бездонному индиго-космосу с акриловым размытием",
        "bg_main": "#060b17",
        "bg_header": "#0b152b",
        "bg_card": "#0f1c38",
        "bg_entry": "#15264c",
        "accent_primary": "#00f0ff",
        "accent_secondary": "#6366f1",
        "accent_glow": "#00d2ff",
        "border_color": "#1e3466",
        "border_glow": "#00f0ff",
        "text_main": "#ffffff",
        "text_muted": "#a5b4fc",
        "text_dim": "#57607a",
        "button_bg": "#0284c7",
        "button_hover": "#4f46e5",
        "success": "#10b981",
        "error": "#f43f5e",
        "bar_active": "#4f46e5",
        "glass_tint": "#060b17",
        "glass_alpha": 220,
    },
    "sky_nebula": {
        "label": "🔮 Звёздная Туманность (Nebula Amethyst)",
        "type": "Градиентный Glass-стиль",
        "desc": "Мистический аметистовый космос: глубокий фиолетовый блюр и неоновый ультрамарин",
        "bg_main": "#0d0918",
        "bg_header": "#170f2b",
        "bg_card": "#20143a",
        "bg_entry": "#2b1c4e",
        "accent_primary": "#c084fc",
        "accent_secondary": "#818cf8",
        "accent_glow": "#a855f7",
        "border_color": "#3b2260",
        "border_glow": "#c084fc",
        "text_main": "#faf5ff",
        "text_muted": "#e9d5ff",
        "text_dim": "#7e6d8a",
        "button_bg": "#7e22ce",
        "button_hover": "#6b21a8",
        "success": "#34d399",
        "error": "#f43f5e",
        "bar_active": "#9333ea",
        "glass_tint": "#0d0918",
        "glass_alpha": 222,
    },
    "sky_twilight": {
        "label": "🌇 Закат в Облаках (Cloud Twilight ➜ Coral)",
        "type": "Градиентный Glass-стиль",
        "desc": "Теплый закат сквозь перисто-кучевые облака: коралловый блюр и мягкий фиалковый закат",
        "bg_main": "#100c1c",
        "bg_header": "#1c1430",
        "bg_card": "#241b3d",
        "bg_entry": "#312552",
        "accent_primary": "#f472b6",
        "accent_secondary": "#fb923c",
        "accent_glow": "#ec4899",
        "border_color": "#4a2862",
        "border_glow": "#f472b6",
        "text_main": "#fff1f2",
        "text_muted": "#fbcfe8",
        "text_dim": "#735c6e",
        "button_bg": "#db2777",
        "button_hover": "#be185d",
        "success": "#4ade80",
        "error": "#ef4444",
        "bar_active": "#db2777",
        "glass_tint": "#100c1c",
        "glass_alpha": 220,
    },
}

API_PRESETS = {
    "together": {
        "label": "Together AI",
        "url": "https://api.together.ai/v1/chat/completions",
        "default_model": "Prism-ML/Ternary-Bonsai-27B",
        "fallback_models": []
    },
    "groq": {
        "label": "⚡ Groq Cloud",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "default_model": "qwen/qwen3.8-27b",
        "fallback_models": [""]
    },
    "openrouter": {
        "label": "🌐 OpenRouter",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "default_model": "nvidia/nemotron-3-ultra-550b-a55b:free",
        "fallback_models": [""]
    },
    "cerebras": {
        "label": "🚀 Cerebras Cloud",
        "url": "https://api.cerebras.ai/v1/chat/completions",
        "default_model": "llama3.3-70b",
        "fallback_models": ["llama3.1-8b"]
    },
    "gemini": {
        "label": "Google Gemini (Native)",
        "url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        "default_model": "gemini-3.5-flash-lite",
        "fallback_models": ["gemini-2.5-flash"]
    },
    "deepseek": {
        "label": "DeepSeek API",
        "url": "https://api.deepseek.com/chat/completions",
        "default_model": "deepseek-chat",
        "fallback_models": []
    },
    "openai": {
        "label": "OpenAI Official",
        "url": "https://api.openai.com/v1/chat/completions",
        "default_model": "gpt-4o-mini",
        "fallback_models": []
    }
}

def get_current_theme() -> dict:
    theme_key = CONFIG.get("ACTIVE_THEME", "sky_azure")
    return CELESTIAL_THEMES.get(theme_key, CELESTIAL_THEMES["sky_azure"])

def persist_runtime_settings():
    def _clean(val):
        return str(val or "").replace("\\", "\\\\").replace('"', '\\"')

    try:
        script_path = os.path.abspath(__file__ if "__file__" in globals() else sys.argv[0])
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()

        for key in ["ACTIVE_PRESET", "API_URL", "MODEL", "API_KEY", "ACTIVE_THEME", "GLOW_MODE"]:
            pattern = rf'("{key}"\s*:\s*")[^"]*(")'
            content = re.sub(pattern, rf'\g<1>{_clean(CONFIG.get(key, ""))}\g<2>', content, count=1)

        for b_key in ["GLASS_BLUR", "SYNC_PIXEL_THEME"]:
            b_val = "True" if CONFIG.get(b_key, True) else "False"
            pattern = rf'("{b_key}"\s*:\s*)(?:True|False)'
            content = re.sub(pattern, rf'\g<1>{b_val}', content, count=1)

        for block_name in ["API_KEYS", "MODELS", "HOTKEYS", "COLORS", "MAGIC_PRINT"]:
            m_block = re.search(rf'("{block_name}"\s*:\s*\{{[^}}]*\}})', content)
            if m_block:
                old_block = m_block.group(1)
                new_block = old_block
                for sub_k, sub_v in CONFIG[block_name].items():
                    if block_name == "MAGIC_PRINT":
                        serialized = json.dumps(sub_v, ensure_ascii=False) if isinstance(sub_v, str) else repr(sub_v)
                        sub_pat = rf'("{re.escape(sub_k)}"\s*:\s*)(?:"(?:\\.|[^"\\])*"|True|False|[-+]?(?:\d+(?:\.\d*)?|\.\d+))'
                        new_block = re.sub(
                            sub_pat,
                            lambda match: match.group(1) + serialized,
                            new_block,
                            count=1,
                        )
                    else:
                        sub_pat = rf'("{sub_k}"\s*:\s*")[^"]*(")'
                        new_block = re.sub(sub_pat, rf'\g<1>{_clean(sub_v)}\g<2>', new_block, count=1)
                content = content.replace(old_block, new_block, 1)

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(content)
        append_log("[CONFIG] Настройки, хоткеи и стиль успешно сохранены в файл.")
    except Exception as exc:
        append_log(f"[WARN] Ошибка сохранения файла: {exc}")

class AppState:
    def __init__(self):
        self.generated_code: str = ""
        self.magic_index: int = 0
        self.magic_mode: bool = False
        self.is_sleeping: bool = False
        self.is_loading: bool = False
        self._is_typing: bool = False
        self.is_destroying: bool = False
        self.magic_stop_event = threading.Event()

        self.last_prompt: str = ""
        self.context_buffer: str = ""
        
        self.root: Optional[tk.Tk] = None
        self.pixel_label: Optional[tk.Label] = None
        self.bar_window: Optional[tk.Toplevel] = None
        self.bar_labels: List[tk.Label] = []

        self.magic_hook = None
        self.settings_window: Optional[tk.Toplevel] = None
        self.status_label: Optional[ttk.Label] = None
        self.log_widget: Optional[tk.Text] = None

state = AppState()

def get_color(name: str) -> str:
    return CONFIG["COLORS"].get(name, CONFIG["COLORS"]["idle"])

def set_pixel_color(color_hex: str):
    if state.root and state.pixel_label and not state.is_destroying:
        try:
            if state.root.winfo_exists():
                state.root.after(0, lambda: state.pixel_label.configure(bg=color_hex))
        except Exception:
            pass

def update_bar_display(remaining_chars: int):
    if not state.bar_labels or not state.root or state.is_destroying:
        return

    active_count = 0
    if remaining_chars > 1200:
        active_count = 5
    elif remaining_chars > 800:
        active_count = 4
    elif remaining_chars > 500:
        active_count = 3
    elif remaining_chars > 300:
        active_count = 2
    elif remaining_chars > 50:
        active_count = 1

    def _apply():
        try:
            for i, lbl in enumerate(state.bar_labels):
                lbl.configure(bg=get_color("bar_active") if i < active_count else get_color("idle"))
        except Exception:
            pass

    state.root.after(0, _apply)

def reset_bar_display():
    update_bar_display(0)

def blink_pixel(color_hex: str, count: int = 2, delay: float = 0.12):
    def _blink():
        prev = get_color("idle")
        for _ in range(count):
            set_pixel_color(color_hex)
            time.sleep(delay)
            set_pixel_color(prev)
            time.sleep(delay)
    threading.Thread(target=_blink, daemon=True).start()

def animate_magic_toggle(turn_on: bool):
    def _run():
        c_on = get_color("ready")
        c_off = get_color("red")
        set_pixel_color(get_color("orange"))
        time.sleep(0.15)
        set_pixel_color(c_on if turn_on else c_off)
        time.sleep(0.20)
        set_pixel_color(get_color("idle"))
    threading.Thread(target=_run, daemon=True).start()

def append_log(message: str):
    if state.log_widget is None or state.is_destroying:
        return

    def _write():
        try:
            state.log_widget.configure(state="normal")
            state.log_widget.insert(tk.END, f"{message}\n")
            state.log_widget.see(tk.END)
            state.log_widget.configure(state="disabled")
            full_txt = state.log_widget.get("1.0", tk.END)
            if len(full_txt) > CONFIG["LOG_LIMIT"]:
                state.log_widget.delete("1.0", f"{len(full_txt) - CONFIG['LOG_LIMIT']} chars")
        except Exception:
            pass

    try:
        state.log_widget.after_idle(_write)
    except Exception:
        pass

def update_status_label():
    if state.status_label is None or state.is_destroying:
        return
    ctx_len = len(state.context_buffer.strip()) if state.context_buffer else 0
    rem = max(0, len(state.generated_code) - state.magic_index)
    text = (f"Код в памяти: {len(state.generated_code)} симв. (осталось: {rem}) | "
            f"Контекст: {ctx_len} симв. | Magic: {'ВКЛ' if state.magic_mode else 'ВЫКЛ'}")
    try:
        state.status_label.after_idle(lambda: state.status_label.config(text=text))
    except Exception:
        pass

def sanitize_ai_code(raw_text: str) -> str:
    if not raw_text:
        return ""
    text = raw_text.strip()

    if text.lower().startswith("user safety:") or text.lower().startswith("safety:"):
        return ""

    text = re.sub(r"(?is)<think>.*?</think>", "", text)
    text = re.sub(r"(?is)```(?:thinking|thought)\b.*?```", "", text)

    blocks = re.findall(r"```(?:\w+)?\s*\n(.*?)\n```", text, flags=re.DOTALL)
    if blocks:
        text = "\n\n".join(b.strip() for b in blocks if b.strip())
    else:
        text = re.sub(r"(?m)^\s*```(?:\w+)?\s*$", "", text)

    text = re.sub(r"(?is)^\s*(?:Here\s+is\s+the\s+code:?|Here\s+is\s+your\s+solution:?|Sure[!,.]?\s*here\s+is.*?:\s*)\s*", "", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.strip()

def send_single_request(url: str, key: str, model: str, system_prompt: str, prompt_text: str, temperature: float) -> Tuple[bool, int, str]:
    is_gemini_native = ("generativelanguage.googleapis.com" in url and "models" in url and "openai" not in url)
    
    if is_gemini_native:
        formatted_url = url.format(model=model)
        full_url = f"{formatted_url}?key={key.strip()}"
        headers = {"Content-Type": "application/json", "x-goog-api-key": key.strip()}
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": prompt_text}]}],
            "generationConfig": {"temperature": float(temperature), "maxOutputTokens": 8192}
        }
    else:
        full_url = url
        headers = {
            "Authorization": f"Bearer {key.strip()}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost",
            "X-Title": "AssistantCore"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_text}
            ],
            "temperature": float(temperature)
        }

    try:
        resp = requests.post(full_url, headers=headers, json=payload, timeout=(6, 30))
        status = resp.status_code

        if status == 200:
            data = resp.json()
            if is_gemini_native:
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    raw_text = "".join([p.get("text", "") for p in parts if isinstance(p, dict)])
                    cleaned = sanitize_ai_code(raw_text)
                    return (True, status, cleaned) if cleaned else (False, status, "Пустой ответ модели.")
                return False, status, "Google вернул пустой candidates."
            else:
                choices = data.get("choices", [])
                if choices:
                    raw_text = choices[0].get("message", {}).get("content", "")
                    cleaned = sanitize_ai_code(raw_text)
                    return (True, status, cleaned) if cleaned else (False, status, "Пустой ответ choices[].")
                return False, status, "choices[] пуст."

        try:
            err_json = resp.json()
            err_msg = err_json.get("error", {}).get("message", resp.text[:180])
        except Exception:
            err_msg = resp.text[:180]

        return False, status, f"HTTP {status}: {err_msg}"

    except requests.exceptions.ConnectTimeout:
        return False, 0, "ConnectTimeout: сервер недоступен."
    except requests.exceptions.ReadTimeout:
        return False, 0, "ReadTimeout: превышен лимит 30 сек."
    except Exception as e:
        return False, 0, f"Сбой сети: {e}"

def request_llm_code(prompt_text: str, temperature: Optional[float] = None) -> Optional[str]:
    api_key = CONFIG["API_KEY"].strip()
    if not api_key:
        append_log("[ОШИБКА] API Key пуст! Откройте настройки (F8) и введите ключ.")
        return None

    if temperature is None:
        temperature = CONFIG["TEMPERATURE"]

    system_prompt = (
        "Output ONLY valid, runnable source code without markdown (no ```), intros, or explanations. "
        "Infer language and solve the user's task directly."
    )

    preset_name = CONFIG["ACTIVE_PRESET"]
    preset_data = API_PRESETS.get(preset_name, {})
    
    models_to_try = [CONFIG["MODEL"]]
    for fb in preset_data.get("fallback_models", []):
        if fb and fb not in models_to_try:
            models_to_try.append(fb)

    for current_model in models_to_try:
        append_log(f"[API] Запрос: {current_model} (t={temperature})...")

        for attempt in range(3):
            success, status_code, result_or_err = send_single_request(
                url=CONFIG["API_URL"],
                key=api_key,
                model=current_model,
                system_prompt=system_prompt,
                prompt_text=prompt_text,
                temperature=temperature
            )

            if success and result_or_err:
                return result_or_err

            if status_code in (429, 500, 502, 503, 504):
                wait_sec = (attempt + 1) * 1.5
                append_log(f"[RETRY] Сервер перегружен ({status_code}). Повтор через {wait_sec:.1f}с...")
                time.sleep(wait_sec)
                continue
            
            if status_code == 404:
                append_log(f"[WARN] Модель '{current_model}' вернула 404. Проверяем следующую...")
                break

            append_log(f"[ERR] Ответ: {result_or_err}")
            break

    append_log("[FAIL] Не удалось получить ответ от модели.")
    return None

def test_api_connection():
    append_log("[TEST] Проверка связи с нейросетью...")
    def _test():
        res = request_llm_code("print('CONNECT_OK')", temperature=0.1)
        if res:
            append_log("[TEST] УСПЕХ! Связь установлена, код успешно получен!")
            blink_pixel(get_color("ready"), count=3)
        else:
            append_log("[TEST] НЕУДАЧА! Проверьте ключ и выбранную модель.")
            blink_pixel(get_color("error"), count=3)
    threading.Thread(target=_test, daemon=True).start()

def safe_release_modifiers():
    t0 = time.time()
    while any(keyboard.is_pressed(k) for k in ["ctrl", "alt", "shift", "windows", "f1", "f2", "f3"]):
        time.sleep(0.015)
        if time.time() - t0 > 0.4:
            break
    for k in ["alt", "ctrl", "shift"]:
        try:
            keyboard.release(k)
        except Exception:
            pass
    time.sleep(0.04)

def get_selected_text() -> Optional[str]:
    safe_release_modifiers()
    try:
        fallback_clip = pyperclip.paste()
    except Exception:
        fallback_clip = ""

    try:
        pyperclip.copy("")
    except Exception:
        pass

    for cmd in ["ctrl+c", "ctrl+insert"]:
        try:
            keyboard.send(cmd)
        except Exception:
            pass
        time.sleep(0.08)
        
        for _ in range(4):
            try:
                text = pyperclip.paste()
                if text and text.strip():
                    return text.strip()
            except Exception:
                time.sleep(0.03)

    if fallback_clip and fallback_clip.strip():
        append_log("[CLIP] Использован текст, уже находившийся в буфере.")
        return fallback_clip.strip()

    return None

def on_send_hotkey():
    if state.is_sleeping or state.is_loading or state.is_destroying:
        return

    def _worker():
        state.is_loading = True
        set_pixel_color(get_color("loading"))
        update_status_label()

        try:
            selected = get_selected_text()
            if not selected:
                append_log("[WARN] Текст не выделен. Выделите задачу перед нажатием.")
                blink_pixel(get_color("error"), count=2)
                set_pixel_color(get_color("idle"))
                return

            full_prompt = (
                f"[CONTEXT]\n{state.context_buffer}\n\n[TASK]\n{selected}"
                if state.context_buffer.strip() else selected
            )
            state.last_prompt = full_prompt

            code = request_llm_code(full_prompt, temperature=CONFIG["TEMPERATURE"])

            if code:
                state.generated_code = code
                state.magic_index = 0
                set_pixel_color(get_color("ready"))
                update_bar_display(len(code))
                append_log(f"[OK] Код сохранен ({len(code)} симв.). Готов к печати.")
                time.sleep(1.5)
                if not state.magic_mode:
                    set_pixel_color(get_color("idle"))
            else:
                set_pixel_color(get_color("error"))
                reset_bar_display()
                time.sleep(2.0)
                set_pixel_color(get_color("idle"))

        finally:
            state.is_loading = False
            update_status_label()

    threading.Thread(target=_worker, daemon=True).start()

def on_retry_hotkey():
    if state.is_sleeping or state.is_loading or not state.last_prompt or state.is_destroying:
        return

    def _worker():
        state.is_loading = True
        set_pixel_color(get_color("loading"))
        update_status_label()

        try:
            code = request_llm_code(state.last_prompt, temperature=0.6)
            if code:
                state.generated_code = code
                state.magic_index = 0
                set_pixel_color(get_color("ready"))
                update_bar_display(len(code))
                append_log(f"[OK] Код обновлен ({len(code)} симв.).")
                time.sleep(1.5)
                if not state.magic_mode:
                    set_pixel_color(get_color("idle"))
            else:
                set_pixel_color(get_color("error"))
                time.sleep(2.0)
                set_pixel_color(get_color("idle"))
        finally:
            state.is_loading = False
            update_status_label()

    threading.Thread(target=_worker, daemon=True).start()

def on_quick_insert():
    if state.is_sleeping or not state.generated_code or state.is_destroying:
        blink_pixel(get_color("error"), count=2)
        return

    def _paste_worker():
        safe_release_modifiers()
        try:
            old_clip = pyperclip.paste()
        except Exception:
            old_clip = ""

        pyperclip.copy(state.generated_code)
        time.sleep(0.06)

        try:
            keyboard.send("ctrl+v")
        except Exception:
            try:
                keyboard.send("shift+insert")
            except Exception:
                pass

        blink_pixel(get_color("ready"), count=1)
        time.sleep(1.2)

        try:
            if old_clip:
                pyperclip.copy(old_clip)
        except Exception:
            pass

    threading.Thread(target=_paste_worker, daemon=True).start()

def clear_generated_code():
    if state.is_sleeping or state.is_destroying:
        return

    if state.magic_mode:
        toggle_magic_mode(force_off=True)

    state.generated_code = ""
    state.magic_index = 0
    reset_bar_display()
    blink_pixel(get_color("orange"), count=2, delay=0.08)
    append_log("[CLEAN] Буфер кода очищен.")
    update_status_label()

def on_add_context():
    if state.is_sleeping or state.is_destroying:
        return
    text = get_selected_text()
    if text:
        state.context_buffer = (state.context_buffer + "\n\n" + text).strip()
        append_log(f"[CTX] Добавлено в контекст (+{len(text)} симв.).")
        blink_pixel(get_color("ready"), count=1)
        update_status_label()

def clear_context_buffer():
    if state.is_destroying:
        return
    state.context_buffer = ""
    append_log("[CTX] Буфер контекста очищен.")
    blink_pixel(get_color("ready"), count=1)
    update_status_label()

def magic_wait(delay: float) -> bool:
    deadline = time.monotonic() + max(0.0, delay)
    while True:
        if state.magic_stop_event.is_set() or not state.magic_mode:
            return False
        if keyboard.is_pressed("esc"):
            state.magic_stop_event.set()
            return False
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return True
        state.magic_stop_event.wait(min(0.025, remaining))

def magic_random_delay(config: dict, minimum_key: str, maximum_key: str) -> float:
    minimum = max(0.0, float(config[minimum_key]))
    maximum = max(minimum, float(config[maximum_key]))
    return random.uniform(minimum, maximum)

def magic_write(text: str):
    state._is_typing = True
    try:
        keyboard.write(text)
    finally:
        state._is_typing = False

def magic_is_auto_indent(text: str, index: int) -> bool:
    if index <= 0 or index >= len(text) or text[index] not in " \t":
        return False
    line_start = text.rfind("\n", 0, index) + 1
    return line_start > 0 and not text[line_start:index].strip(" \t")

def simulate_magic_print():
    text = state.generated_code
    settings = CONFIG["MAGIC_PRINT"]
    total_len = len(text)
    completed = False
    cancelled = False

    try:
        if not magic_wait(magic_random_delay(settings, "thinking_pause_min", "thinking_pause_max")):
            cancelled = True
            return

        for index in range(state.magic_index, total_len):
            char = text[index]
            if settings.get("skip_auto_indent", True) and magic_is_auto_indent(text, index):
                state.magic_index = index + 1
                continue

            if not magic_wait(magic_random_delay(settings, "key_delay_min", "key_delay_max")):
                cancelled = True
                break

            if char == "\r":
                state.magic_index = index + 1
                if index + 1 < total_len and text[index + 1] == "\n":
                    continue
                char = "\n"
            if char.isalpha() and random.random() < float(settings["error_probability"]) / 100:
                alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if char.isupper() else "abcdefghijklmnopqrstuvwxyz"
                wrong_char = random.choice(alphabet.replace(char, ""))
                magic_write(wrong_char)
                if not magic_wait(magic_random_delay(settings, "typo_hold_min", "typo_hold_max")):
                    keyboard.send("backspace")
                    cancelled = True
                    break
                keyboard.send("backspace")
                if not magic_wait(magic_random_delay(settings, "erase_delay_min", "erase_delay_max")):
                    cancelled = True
                    break
                if not magic_wait(magic_random_delay(settings, "correction_delay_min", "correction_delay_max")):
                    cancelled = True
                    break

            magic_write(char)
            state.magic_index = index + 1

            if char in " \t" and text[text.rfind("\n", 0, index) + 1:index].strip():
                if not magic_wait(magic_random_delay(settings, "space_delay_min", "space_delay_max")):
                    cancelled = True
                    break
            elif char in ".,;:!?)]}":
                if not magic_wait(magic_random_delay(settings, "punctuation_delay_min", "punctuation_delay_max")):
                    cancelled = True
                    break
            elif char == "\n":
                if not magic_wait(magic_random_delay(settings, "newline_delay_min", "newline_delay_max")):
                    cancelled = True
                    break

            next_char = text[index + 1] if index + 1 < total_len else ""
            word_ended = char.isalnum() or char in ".,;:!?)]}"
            if word_ended and (not next_char or next_char.isspace()):
                if random.random() < float(settings["word_pause_probability"]) / 100:
                    if not magic_wait(magic_random_delay(settings, "word_pause_min", "word_pause_max")):
                        cancelled = True
                        break
                if random.random() < float(settings["thinking_probability"]) / 100:
                    if not magic_wait(magic_random_delay(settings, "thinking_pause_min", "thinking_pause_max")):
                        cancelled = True
                        break

            if state.magic_index % 10 == 0 or state.magic_index == total_len:
                update_bar_display(total_len - state.magic_index)

        completed = state.magic_index >= total_len and state.magic_mode and not state.magic_stop_event.is_set()
    except Exception as exc:
        append_log(f"[ERROR] Ошибка симуляции Magic Print: {exc}")
        blink_pixel(get_color("error"), count=2)
    finally:
        state._is_typing = False
        if completed:
            append_log("[MAGIC] Симуляция печати завершена.")
        elif cancelled or state.magic_stop_event.is_set():
            append_log(f"[MAGIC] Симуляция остановлена на символе {state.magic_index + 1}.")
        if state.magic_mode:
            toggle_magic_mode(force_off=True)

def magic_keyboard_hook(event):
    if event.event_type != keyboard.KEY_DOWN:
        return True

    if state._is_typing or state.is_destroying:
        return True

    if event.name in ["ctrl", "alt", "shift", "windows", "esc", "tab"]:
        return True

    if keyboard.is_pressed("ctrl") or keyboard.is_pressed("shift"):
        return True

    if state.magic_mode and state.generated_code:
        total_len = len(state.generated_code)
        
        if state.magic_index < total_len:
            if CONFIG["MAGIC_PRINT"].get("skip_auto_indent", True):
                while magic_is_auto_indent(state.generated_code, state.magic_index):
                    state.magic_index += 1
                if state.magic_index >= total_len:
                    reset_bar_display()
                    threading.Thread(target=lambda: toggle_magic_mode(force_off=True), daemon=True).start()
                    return False

            chunk_size = max(1, CONFIG.get("MAGIC_CHUNK_SIZE", 1))
            end_idx = min(total_len, state.magic_index + chunk_size)
            chars_to_type = state.generated_code[state.magic_index:end_idx]
            state.magic_index = end_idx
            remaining = total_len - state.magic_index

            state._is_typing = True
            try:
                keyboard.write(chars_to_type)
            finally:
                state._is_typing = False

            if remaining % 5 == 0 or remaining <= 10:
                update_bar_display(remaining)

            if state.magic_index >= total_len:
                reset_bar_display()
                threading.Thread(target=lambda: toggle_magic_mode(force_off=True), daemon=True).start()

            return False
        else:
            reset_bar_display()
            threading.Thread(target=lambda: toggle_magic_mode(force_off=True), daemon=True).start()
            return True

    return True

def toggle_magic_mode(force_off: bool = False):
    if state.is_sleeping or state.is_destroying:
        return

    target_state = False if force_off else not state.magic_mode

    if target_state and not state.generated_code:
        blink_pixel(get_color("error"), count=2)
        append_log("[WARN] Нет кода в памяти для Magic Print.")
        return

    if state.magic_mode == target_state:
        return

    state.magic_mode = target_state

    if state.magic_mode:
        state.magic_stop_event.clear()
        animate_magic_toggle(turn_on=True)
        mode = CONFIG["MAGIC_PRINT"].get("mode", "simulation")
        mode_name = "Симуляция" if mode == "simulation" else "Пошаговый режим"
        append_log(f"[MAGIC] Магическая печать: ВКЛ. Режим: {mode_name}.")
        rem = len(state.generated_code) - state.magic_index
        update_bar_display(rem)

        if mode == "simulation":
            threading.Thread(target=simulate_magic_print, daemon=True).start()
        elif state.magic_hook is None:
            state.magic_hook = keyboard.hook(magic_keyboard_hook, suppress=True)
    else:
        state.magic_stop_event.set()
        animate_magic_toggle(turn_on=False)
        append_log("[MAGIC] Магическая печать: ВЫКЛ.")
        
        if state.magic_index >= len(state.generated_code):
            reset_bar_display()

        if state.magic_hook is not None:
            try:
                keyboard.unhook(state.magic_hook)
            except Exception:
                pass
            state.magic_hook = None

    update_status_label()

def panic_sleep_toggle():
    if state.is_destroying:
        return

    if not state.is_sleeping:
        state.is_sleeping = True
        toggle_magic_mode(force_off=True)
        set_pixel_color(get_color("idle"))
        reset_bar_display()

        if state.root:
            state.root.after(0, state.root.withdraw)
        if state.bar_window:
            state.bar_window.after(0, state.bar_window.withdraw)

        append_log("[PANIC] Анабиоз активен на 5 минут.")

        def _timer():
            for _ in range(300):
                if not state.is_sleeping or state.is_destroying:
                    return
                time.sleep(1)
            state.is_sleeping = False
            if state.root and not state.is_destroying:
                state.root.after(0, state.root.deiconify)
                blink_pixel(get_color("ready"), count=2)
            if state.bar_window and not state.is_destroying:
                state.bar_window.after(0, state.bar_window.deiconify)
            append_log("[PANIC] Пробуждение.")

        threading.Thread(target=_timer, daemon=True).start()
    else:
        state.is_sleeping = False
        if state.root:
            state.root.after(0, state.root.deiconify)
            blink_pixel(get_color("ready"), count=2)
        if state.bar_window:
            state.bar_window.after(0, state.bar_window.deiconify)
        append_log("[PANIC] Досрочный выход из анабиоза.")

def panic_self_destruct():
    if state.is_destroying:
        return
    state.is_destroying = True

    try:
        try:
            keyboard.unhook_all()
        except Exception:
            pass

        script_path = os.path.abspath(__file__ if "__file__" in globals() else sys.argv[0])

        if sys.platform == "win32":
            bat_dir = tempfile.gettempdir()
            bat_path = os.path.join(bat_dir, f"cleaner_{int(time.time())}.bat")
            bat_content = f"""@echo off
timeout /t 1 /nobreak > nul
:retry
del /f /q "{script_path}" > nul 2>&1
if exist "{script_path}" (
    timeout /t 1 /nobreak > nul
    goto retry
)
del /f /q "%~f0" > nul 2>&1
"""
            with open(bat_path, "w", encoding="cp866", errors="ignore") as f:
                f.write(bat_content)

            subprocess.Popen(
                ["cmd.exe", "/c", bat_path],
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
            )
        else:
            subprocess.Popen(f'(sleep 1 && rm -f "{script_path}") &', shell=True)

    except Exception:
        pass
    finally:
        os._exit(0)

def hex_to_bgr(hex_col: str) -> int:
    c = hex_col.lstrip('#')
    r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    return (b << 16) | (g << 8) | r

class ACCENT_POLICY(ctypes.Structure):
    _fields_ = [
        ('AccentState', ctypes.c_int),
        ('AccentFlags', ctypes.c_int),
        ('GradientColor', ctypes.c_int),
        ('AnimationId', ctypes.c_int)
    ]

class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
    _fields_ = [
        ('Attribute', ctypes.c_int),
        ('Data', ctypes.c_void_p),
        ('SizeOfData', ctypes.c_size_t)
    ]

def enable_window_acrylic_blur(hwnd: int, bgr_color: int, alpha: int = 220) -> bool:
    """
    Включает аппаратный эффект матового стекла (Acrylic Blur) Windows 10/11.
    """
    try:
        user32 = ctypes.windll.user32
        if not hasattr(user32, "SetWindowCompositionAttribute"):
            return False

        accent = ACCENT_POLICY()
        accent.AccentState = 4  # ACCENT_ENABLE_ACRYLICBLURBEHIND (или 3 ACCENT_ENABLE_BLURBEHIND)
        accent.AccentFlags = 2
        accent.GradientColor = ((alpha & 0xFF) << 24) | (bgr_color & 0xFFFFFF)
        accent.AnimationId = 0

        data = WINDOWCOMPOSITIONATTRIBDATA()
        data.Attribute = 19  # WCA_ACCENT_POLICY
        data.Data = ctypes.cast(ctypes.pointer(accent), ctypes.c_void_p)
        data.SizeOfData = ctypes.sizeof(accent)

        res = user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))
        return bool(res)
    except Exception:
        return False

def apply_celestial_window_style(win: tk.Toplevel, theme: dict):
    """
    Настраивает DWM Windows и матовое стекло:
    1. Включает эффект матового стекла (Acrylic Blur) на уровне Windows.
    2. Окрашивает верхний бар окна в цвет темы (DWMWA_CAPTION_COLOR = 35) в тон стеклу.
    3. Окрашивает заголовок (DWMWA_TEXT_COLOR = 36) в акцентный небесный цвет.
    4. Добавляет скругления (DWMWA_WINDOW_CORNER_PREFERENCE = 33).
    5. Окрашивает рамку окна со свечением (DWMWA_BORDER_COLOR = 34).
    """
    if sys.platform != "win32":
        return
    try:
        win.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
        if not hwnd:
            hwnd = win.winfo_id()

        # Dark Mode (20)
        val = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(val), ctypes.sizeof(val))

        # Скругления окон Windows 11 (33: DWMWCP_ROUND)
        corner = ctypes.c_int(2)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(corner), ctypes.sizeof(corner))

        # Цвет неоновой границы окна (34)
        border_col = ctypes.c_int(hex_to_bgr(theme.get("border_glow", "#38bdf8")))
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 34, ctypes.byref(border_col), ctypes.sizeof(border_col))

        # Цвет заголовка окна (35)
        caption_col = ctypes.c_int(hex_to_bgr(theme.get("bg_header", "#0c182b")))
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(caption_col), ctypes.sizeof(caption_col))

        # Цвет текста заголовка (36)
        text_col = ctypes.c_int(hex_to_bgr(theme.get("accent_primary", "#38bdf8")))
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 36, ctypes.byref(text_col), ctypes.sizeof(text_col))

        # Акриловый матовый блюр
        if CONFIG.get("GLASS_BLUR", True):
            tint_hex = theme.get("glass_tint", theme.get("bg_main", "#070e18"))
            tint_bgr = hex_to_bgr(tint_hex)
            alpha_val = theme.get("glass_alpha", 220)
            enable_window_acrylic_blur(hwnd, tint_bgr, alpha=alpha_val)
            try:
                win.attributes("-alpha", CONFIG.get("GLASS_OPACITY", 0.94))
            except Exception:
                pass
    except Exception:
        pass

def show_settings_menu():
    if state.is_sleeping or state.is_destroying:
        return

    if state.settings_window and state.settings_window.winfo_exists():
        state.settings_window.focus_force()
        return

    menu_win = tk.Toplevel(state.root)
    state.settings_window = menu_win
    menu_win.title("✦ AssistantCore • Celestial Control Panel")
    
    # Центрирование окна на экране
    sw = menu_win.winfo_screenwidth()
    sh = menu_win.winfo_screenheight()
    win_w, win_h = 780, 710
    pos_x = max(10, (sw - win_w) // 2)
    pos_y = max(10, (sh - win_h) // 2 - 25)
    menu_win.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
    menu_win.attributes("-topmost", True)
    menu_win.resizable(False, False)

    current_theme = get_current_theme()
    menu_win.configure(bg=current_theme["bg_main"])
    apply_celestial_window_style(menu_win, current_theme)

    def _on_close():
        state.settings_window = None
        menu_win.destroy()

    menu_win.bind("<Escape>", lambda e: _on_close())
    menu_win.protocol("WM_DELETE_WINDOW", _on_close)

    style = ttk.Style(menu_win)
    style.theme_use("clam")

    def configure_ttk_styles(th: dict):
        bg = th["bg_main"]
        card = th["bg_card"]
        entry = th["bg_entry"]
        text = th["text_main"]
        muted = th["text_muted"]
        accent = th["accent_primary"]
        btn_bg = th["button_bg"]
        btn_hover = th["button_hover"]

        style.configure(".", background=bg, foreground=text, font=("Segoe UI", 9))
        style.configure("TFrame", background=bg)
        style.configure("Card.TFrame", background=card)
        style.configure("TLabel", background=bg, foreground=text, font=("Segoe UI", 9))
        style.configure("Card.TLabel", background=card, foreground=text, font=("Segoe UI", 9))
        style.configure("Header.TLabel", font=("Segoe UI", 11, "bold"), foreground=accent, background=card)
        style.configure("Sub.TLabel", font=("Segoe UI", 8), foreground=muted, background=card)
        style.configure("Status.TLabel", font=("Segoe UI", 9, "bold"), foreground=th["success"], background=card)

        style.configure("TNotebook", background=bg, borderwidth=0)
        style.configure("TNotebook.Tab", background=th["bg_header"], foreground=muted, padding=[18, 8], font=("Segoe UI", 9, "bold"), borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", card), ("active", entry)], foreground=[("selected", accent), ("active", "#ffffff")])

        style.configure("TEntry", fieldbackground=entry, foreground=text, insertcolor=accent, borderwidth=0)
        style.configure("TCombobox", fieldbackground=entry, foreground=text, selectbackground=entry, borderwidth=0, arrowcolor=accent)
        style.map("TCombobox", fieldbackground=[("readonly", entry)], selectbackground=[("readonly", entry)])

        style.configure("Card.TCheckbutton", background=card, foreground=muted, font=("Segoe UI", 9))
        style.map("Card.TCheckbutton", background=[("active", card)], foreground=[("active", text)])

        style.configure("Primary.TButton", background=btn_bg, foreground="#ffffff", borderwidth=0, padding=[12, 8], font=("Segoe UI", 9, "bold"))
        style.map("Primary.TButton", background=[("active", btn_hover), ("pressed", th["accent_secondary"])])

        style.configure("Dark.TButton", background=th["bg_header"], foreground=text, borderwidth=0, padding=[12, 8], font=("Segoe UI", 9, "bold"))
        style.map("Dark.TButton", background=[("active", card), ("pressed", entry)])

    configure_ttk_styles(current_theme)

    # --- ВЕРХНИЙ НЕБЕСНЫЙ ХЕДЕР (Устраняет черный бар и дает аппаратное перетаскивание без лагов) ---
    header_frame = tk.Frame(menu_win, bg=current_theme["bg_header"], height=52)
    header_frame.pack(fill=tk.X, side=tk.TOP)
    header_frame.pack_propagate(False)

    def _start_window_drag(event):
        if sys.platform == "win32":
            try:
                ctypes.windll.user32.ReleaseCapture()
                hwnd = ctypes.windll.user32.GetParent(menu_win.winfo_id()) or menu_win.winfo_id()
                ctypes.windll.user32.SendMessageW(hwnd, 0xA1, 2, 0)
            except Exception:
                pass

    header_frame.bind("<Button-1>", _start_window_drag)

    h_left = tk.Frame(header_frame, bg=current_theme["bg_header"])
    h_left.pack(side=tk.LEFT, padx=14, pady=6)
    h_left.bind("<Button-1>", _start_window_drag)

    lbl_icon = tk.Label(h_left, text="✦", font=("Segoe UI", 16, "bold"), fg=current_theme["accent_primary"], bg=current_theme["bg_header"])
    lbl_icon.pack(side=tk.LEFT, padx=(0, 8))
    lbl_icon.bind("<Button-1>", _start_window_drag)

    lbl_title_box = tk.Frame(h_left, bg=current_theme["bg_header"])
    lbl_title_box.pack(side=tk.LEFT)
    lbl_title_box.bind("<Button-1>", _start_window_drag)

    lbl_main_title = tk.Label(lbl_title_box, text="ASSISTANT CORE", font=("Segoe UI", 11, "bold"), fg=current_theme["text_main"], bg=current_theme["bg_header"])
    lbl_main_title.pack(anchor=tk.W)
    lbl_main_title.bind("<Button-1>", _start_window_drag)

    lbl_sub_title = tk.Label(lbl_title_box, text="CELESTIAL SKY EDITION • НЕЛЕТУЧИЙ АССИСТЕНТ", font=("Segoe UI", 7, "bold"), fg=current_theme["text_muted"], bg=current_theme["bg_header"])
    lbl_sub_title.pack(anchor=tk.W)
    lbl_sub_title.bind("<Button-1>", _start_window_drag)

    h_right = tk.Frame(header_frame, bg=current_theme["bg_header"])
    h_right.pack(side=tk.RIGHT, padx=14, pady=10)
    h_right.bind("<Button-1>", _start_window_drag)

    status_badge = tk.Label(h_right, text="● СИСТЕМА АКТИВНА", font=("Segoe UI", 8, "bold"), fg=current_theme["success"], bg=current_theme["bg_card"], padx=10, pady=3, bd=0)
    status_badge.pack(side=tk.RIGHT)
    status_badge.bind("<Button-1>", _start_window_drag)

    # Неоновая разделительная полоска под хедером
    header_separator = tk.Frame(menu_win, bg=current_theme["accent_primary"], height=1)
    header_separator.pack(fill=tk.X, side=tk.TOP)

    # --- ВКЛАДКИ NOTEBOOK ---
    notebook = ttk.Notebook(menu_win)
    notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=(10, 6))

    tab_api = ttk.Frame(notebook, style="Card.TFrame", padding=14)
    tab_hotkeys = ttk.Frame(notebook, style="Card.TFrame", padding=14)
    tab_magic = ttk.Frame(notebook, style="Card.TFrame", padding=14)
    tab_styles = ttk.Frame(notebook, style="Card.TFrame", padding=14)

    notebook.add(tab_api, text=" ✦ Сервис и Модель ")
    notebook.add(tab_hotkeys, text=" ⌨️ Хоткеи ")
    notebook.add(tab_magic, text=" ⌨ Симуляция ")
    notebook.add(tab_styles, text=" 🎨 Небесные Стили ")

    # ================= TAB 1: API & МОДЕЛИ =================
    ttk.Label(tab_api, text="Конфигурация нейросети", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 6))

    ttk.Label(tab_api, text="Провайдер нейросети:", style="Card.TLabel").pack(anchor=tk.W, pady=(2, 2))
    preset_var = tk.StringVar(value=CONFIG["ACTIVE_PRESET"])
    preset_combo = ttk.Combobox(tab_api, textvariable=preset_var, state="readonly")
    preset_combo["values"] = list(API_PRESETS.keys())
    preset_combo.pack(fill=tk.X, pady=(0, 6))

    ttk.Label(tab_api, text="API URL:", style="Card.TLabel").pack(anchor=tk.W)
    url_entry = ttk.Entry(tab_api)
    url_entry.insert(0, CONFIG["API_URL"])
    url_entry.pack(fill=tk.X, pady=(0, 6))

    key_frame = ttk.Frame(tab_api, style="Card.TFrame")
    key_frame.pack(fill=tk.X, pady=(0, 2))
    ttk.Label(key_frame, text="API Key:", style="Card.TLabel").pack(side=tk.LEFT)
    
    show_key_var = tk.BooleanVar(value=False)
    def _toggle_key_vis():
        key_entry.configure(show="" if show_key_var.get() else "*")

    show_chk = ttk.Checkbutton(key_frame, text="Показать ключ", variable=show_key_var, command=_toggle_key_vis, style="Card.TCheckbutton")
    show_chk.pack(side=tk.RIGHT)

    key_entry = ttk.Entry(tab_api, show="*")
    key_entry.insert(0, CONFIG["API_KEY"])
    key_entry.pack(fill=tk.X, pady=(0, 6))

    ttk.Label(tab_api, text="Имя модели:", style="Card.TLabel").pack(anchor=tk.W)
    model_entry = ttk.Entry(tab_api)
    model_entry.insert(0, CONFIG["MODEL"])
    model_entry.pack(fill=tk.X, pady=(0, 8))

    def on_preset_select(event=None):
        prev_sel = CONFIG["ACTIVE_PRESET"]
        CONFIG["API_KEYS"][prev_sel] = key_entry.get().strip()
        CONFIG["MODELS"][prev_sel] = model_entry.get().strip()

        sel = preset_var.get()
        preset = API_PRESETS.get(sel, {})
        CONFIG["ACTIVE_PRESET"] = sel
        CONFIG["API_URL"] = preset.get("url", CONFIG["API_URL"])
        
        saved_model = CONFIG["MODELS"].get(sel, preset.get("default_model", ""))
        CONFIG["MODEL"] = saved_model
        CONFIG["API_KEY"] = CONFIG["API_KEYS"].get(sel, "")

        url_entry.delete(0, tk.END)
        url_entry.insert(0, CONFIG["API_URL"])
        model_entry.delete(0, tk.END)
        model_entry.insert(0, CONFIG["MODEL"])
        key_entry.delete(0, tk.END)
        key_entry.insert(0, CONFIG["API_KEY"])
        append_log(f"[PRESET] Переключено на: {preset.get('label', sel)}")

    preset_combo.bind("<<ComboboxSelected>>", on_preset_select)

    status_lbl = ttk.Label(tab_api, text="", style="Status.TLabel")
    state.status_label = status_lbl
    update_status_label()
    status_lbl.pack(anchor=tk.W, pady=(0, 4))

    ttk.Label(tab_api, text="Системный лог:", style="Card.TLabel").pack(anchor=tk.W)
    log_text = tk.Text(tab_api, height=5, wrap=tk.NONE, state="disabled", 
                       bg=current_theme["bg_main"], fg=current_theme["text_muted"], 
                       insertbackground=current_theme["accent_primary"], bd=0, padx=8, pady=4, 
                       font=("Consolas", 8), selectbackground=current_theme["button_bg"])
    state.log_widget = log_text
    
    log_scroll = ttk.Scrollbar(tab_api, orient=tk.VERTICAL, command=log_text.yview)
    log_text.configure(yscrollcommand=log_scroll.set)
    log_scroll.pack(fill=tk.Y, side=tk.RIGHT)
    log_text.pack(fill=tk.BOTH, expand=True, pady=(2, 4))

    # ================= TAB 2: ХОТКЕИ =================
    ttk.Label(tab_hotkeys, text="Настройка клавиатурных комбинаций", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 8))
    
    hotkey_entries = {}
    hk_labels = {
        "send": "Запрос решения по выделению:",
        "magic_print": "Magic Print (пошагово/симуляция):",
        "quick_insert": "Мгновенная вставка (Ctrl+V):",
        "clear_code": "Очистить буфер кода (Drop):",
        "add_context": "Добавить выделение в контекст:",
        "clear_context": "Очистить весь контекст:",
        "retry": "Повторить последнюю генерацию:",
        "menu": "Открыть это меню настроек:",
        "panic_sleep": "Анабиоз (сон) на 5 минут:",
        "panic_kill": "Экстренное стирание с диска:",
    }

    hk_grid = ttk.Frame(tab_hotkeys, style="Card.TFrame")
    hk_grid.pack(fill=tk.BOTH, expand=True)

    row_i = 0
    for key_name, label_text in hk_labels.items():
        ttk.Label(hk_grid, text=label_text, style="Card.TLabel").grid(row=row_i, column=0, sticky=tk.W, pady=3, padx=(0, 10))
        entry = ttk.Entry(hk_grid, width=28)
        entry.insert(0, CONFIG["HOTKEYS"].get(key_name, ""))
        entry.grid(row=row_i, column=1, sticky=tk.E, pady=3)
        hotkey_entries[key_name] = entry
        row_i += 1

    # ================= TAB 3: MAGIC PRINT =================
    ttk.Label(tab_magic, text="Режим и поведение Magic Print", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 4))
    ttk.Label(
        tab_magic,
        text="Пошаговый режим печатает по нажатию клавиши. Симуляция печатает автоматически; Esc или повторный хоткей останавливает печать.",
        style="Sub.TLabel",
        wraplength=700,
    ).pack(anchor=tk.W, pady=(0, 10))

    magic_mode_frame = ttk.Frame(tab_magic, style="Card.TFrame")
    magic_mode_frame.pack(fill=tk.X, pady=(0, 8))
    ttk.Label(magic_mode_frame, text="Режим:", style="Card.TLabel").pack(side=tk.LEFT, padx=(0, 10))
    magic_mode_labels = {
        "step": "Пошаговый (по нажатию клавиши)",
        "simulation": "Симуляция (автоматическая печать)",
    }
    magic_mode_var = tk.StringVar(
        value=magic_mode_labels.get(
            CONFIG["MAGIC_PRINT"].get("mode", "simulation"),
            magic_mode_labels["simulation"],
        )
    )
    magic_mode_combo = ttk.Combobox(
        magic_mode_frame,
        textvariable=magic_mode_var,
        values=list(magic_mode_labels.values()),
        state="readonly",
    )
    magic_mode_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

    skip_auto_indent_var = tk.BooleanVar(value=CONFIG["MAGIC_PRINT"].get("skip_auto_indent", True))
    ttk.Checkbutton(
        tab_magic,
        text="Пропускать отступ после Enter, если редактор добавляет его сам",
        variable=skip_auto_indent_var,
        style="Card.TCheckbutton",
    ).pack(anchor=tk.W, pady=(0, 8))

    magic_settings_frame = ttk.Frame(tab_magic, style="Card.TFrame")
    magic_settings_frame.pack(fill=tk.BOTH, expand=True)
    magic_settings_frame.grid_columnconfigure(0, weight=1)

    ttk.Label(magic_settings_frame, text="Параметр", style="Card.TLabel").grid(row=0, column=0, sticky=tk.W, pady=(0, 4))
    ttk.Label(magic_settings_frame, text="Минимум, сек.", style="Card.TLabel").grid(row=0, column=1, padx=6, pady=(0, 4))
    ttk.Label(magic_settings_frame, text="Максимум, сек.", style="Card.TLabel").grid(row=0, column=2, padx=6, pady=(0, 4))

    magic_delay_fields = [
        ("Интервал между символами", "key_delay_min", "key_delay_max"),
        ("Дополнительная пауза на пробелах/табах", "space_delay_min", "space_delay_max"),
        ("Пауза после знаков препинания", "punctuation_delay_min", "punctuation_delay_max"),
        ("Пауза после перехода на новую строку", "newline_delay_min", "newline_delay_max"),
        ("Как долго видна опечатка до удаления", "typo_hold_min", "typo_hold_max"),
        ("Пауза после удаления опечатки", "erase_delay_min", "erase_delay_max"),
        ("Пауза перед исправленным символом", "correction_delay_min", "correction_delay_max"),
        ("Случайная пауза после слова", "word_pause_min", "word_pause_max"),
        ("Пауза-размышление после слова", "thinking_pause_min", "thinking_pause_max"),
    ]
    magic_entries = {}
    magic_config = CONFIG["MAGIC_PRINT"]
    for row, (label, min_key, max_key) in enumerate(magic_delay_fields, start=1):
        ttk.Label(magic_settings_frame, text=label, style="Card.TLabel").grid(row=row, column=0, sticky=tk.W, pady=3, padx=(0, 8))
        min_entry = ttk.Entry(magic_settings_frame, width=12)
        min_entry.insert(0, f"{float(magic_config[min_key]):g}")
        min_entry.grid(row=row, column=1, padx=6, pady=3)
        max_entry = ttk.Entry(magic_settings_frame, width=12)
        max_entry.insert(0, f"{float(magic_config[max_key]):g}")
        max_entry.grid(row=row, column=2, padx=6, pady=3)
        magic_entries[min_key] = min_entry
        magic_entries[max_key] = max_entry

    magic_probability_fields = [
        ("Шанс опечатки на букве (%)", "error_probability"),
        ("Шанс паузы после слова (%)", "word_pause_probability"),
        ("Шанс паузы-размышления (%)", "thinking_probability"),
    ]
    probability_start_row = len(magic_delay_fields) + 1
    for row, (label, key) in enumerate(magic_probability_fields, start=probability_start_row):
        ttk.Label(magic_settings_frame, text=label, style="Card.TLabel").grid(row=row, column=0, sticky=tk.W, pady=3, padx=(0, 8))
        entry = ttk.Entry(magic_settings_frame, width=12)
        entry.insert(0, f"{float(magic_config[key]):g}")
        entry.grid(row=row, column=1, sticky=tk.W, padx=6, pady=3)
        magic_entries[key] = entry

    # ================= TAB 4: НЕБЕСНЫЕ СТИЛИ =================
    ttk.Label(tab_styles, text="Небесные визуальные стили и подсветка", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 4))
    ttk.Label(tab_styles, text="Выберите палитру мягкой подсветки или градиента. Применяется моментально.", style="Sub.TLabel").pack(anchor=tk.W, pady=(0, 10))

    theme_select_frame = ttk.Frame(tab_styles, style="Card.TFrame")
    theme_select_frame.pack(fill=tk.X, pady=(0, 10))

    ttk.Label(theme_select_frame, text="Текущий небесный стиль:", style="Card.TLabel").pack(anchor=tk.W, pady=(0, 2))
    
    theme_var = tk.StringVar(value=CONFIG.get("ACTIVE_THEME", "sky_azure"))
    theme_names = {k: v["label"] for k, v in CELESTIAL_THEMES.items()}
    theme_keys_by_label = {v["label"]: k for k, v in CELESTIAL_THEMES.items()}

    theme_combo = ttk.Combobox(theme_select_frame, values=list(theme_names.values()), state="readonly")
    curr_label = CELESTIAL_THEMES.get(theme_var.get(), CELESTIAL_THEMES["sky_azure"])["label"]
    theme_combo.set(curr_label)
    theme_combo.pack(fill=tk.X, pady=(0, 6))

    desc_lbl = ttk.Label(theme_select_frame, text=CELESTIAL_THEMES[theme_var.get()]["desc"], style="Sub.TLabel")
    desc_lbl.pack(anchor=tk.W, pady=(0, 8))

    # Чекбокс стеклянного блюра и синхронизации со статус-пикселем
    glass_ctrl_frame = ttk.Frame(theme_select_frame, style="Card.TFrame")
    glass_ctrl_frame.pack(fill=tk.X, pady=(0, 6))

    glass_blur_var = tk.BooleanVar(value=CONFIG.get("GLASS_BLUR", True))
    def on_glass_toggle():
        CONFIG["GLASS_BLUR"] = glass_blur_var.get()
        th = CELESTIAL_THEMES.get(theme_var.get(), CELESTIAL_THEMES["sky_azure"])
        apply_celestial_window_style(menu_win, th)

    glass_blur_chk = ttk.Checkbutton(glass_ctrl_frame, text="✨ Матовое акриловое стекло (Windows Acrylic Blur)", 
                                     variable=glass_blur_var, command=on_glass_toggle, style="Card.TCheckbutton")
    glass_blur_chk.pack(anchor=tk.W, pady=(0, 3))

    sync_pixel_var = tk.BooleanVar(value=CONFIG.get("SYNC_PIXEL_THEME", True))
    sync_pixel_chk = ttk.Checkbutton(glass_ctrl_frame, text="Синхронизировать цвета экранного пикселя и индикатора со стилем", 
                                     variable=sync_pixel_var, style="Card.TCheckbutton")
    sync_pixel_chk.pack(anchor=tk.W, pady=(0, 6))

    def live_apply_theme(new_theme_key: str):
        th = CELESTIAL_THEMES.get(new_theme_key, CELESTIAL_THEMES["sky_azure"])
        CONFIG["ACTIVE_THEME"] = new_theme_key
        
        # Обновление окна и стилей
        menu_win.configure(bg=th["bg_main"])
        configure_ttk_styles(th)
        apply_celestial_window_style(menu_win, th)

        # Обновление хедера
        header_frame.configure(bg=th["bg_header"])
        h_left.configure(bg=th["bg_header"])
        lbl_icon.configure(fg=th["accent_primary"], bg=th["bg_header"])
        lbl_title_box.configure(bg=th["bg_header"])
        lbl_main_title.configure(fg=th["text_main"], bg=th["bg_header"])
        lbl_sub_title.configure(fg=th["text_muted"], bg=th["bg_header"])
        h_right.configure(bg=th["bg_header"])
        status_badge.configure(fg=th["success"], bg=th["bg_card"])
        header_separator.configure(bg=th["accent_primary"])

        # Обновление логов
        log_text.configure(bg=th["bg_main"], fg=th["text_muted"], insertbackground=th["accent_primary"], selectbackground=th["button_bg"])

        # Обновление описания выбранного стиля
        desc_lbl.configure(text=th["desc"])

        # Синхронизация пикселей на экране если включено
        if sync_pixel_var.get():
            CONFIG["COLORS"]["idle"] = th["bg_main"]
            CONFIG["COLORS"]["loading"] = th["accent_primary"]
            CONFIG["COLORS"]["ready"] = th["success"]
            CONFIG["COLORS"]["bar_active"] = th["bar_active"]
            set_pixel_color(th["bg_main"])
            if state.bar_window:
                state.bar_window.configure(bg=th["bg_main"])

        append_log(f"[THEME] Небесный стиль изменен на: {th['label']}")

    def on_theme_select(event=None):
        selected_label = theme_combo.get()
        new_key = theme_keys_by_label.get(selected_label, "sky_azure")
        theme_var.set(new_key)
        live_apply_theme(new_key)

    theme_combo.bind("<<ComboboxSelected>>", on_theme_select)

    # --- НИЖНЯЯ ПАНЕЛЬ С КНОПКАМИ ---
    btn_frame = ttk.Frame(menu_win, padding=12)
    btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

    ttk.Button(btn_frame, text="⚡ Проверить связь с API", style="Dark.TButton", command=test_api_connection).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

    def save_and_close():
        try:
            magic_values = {key: float(entry.get().strip()) for key, entry in magic_entries.items()}
            for _, min_key, max_key in magic_delay_fields:
                if not (0 <= magic_values[min_key] <= magic_values[max_key] <= 60):
                    raise ValueError("Для каждой задержки нужно указать значения от 0 до 60 секунд и минимум не больше максимума.")
            for _, key in magic_probability_fields:
                if not 0 <= magic_values[key] <= 100:
                    raise ValueError("Вероятности должны быть в диапазоне от 0 до 100%.")
            selected_mode = next(
                key for key, label in magic_mode_labels.items()
                if label == magic_mode_combo.get()
            )
        except (ValueError, StopIteration) as exc:
            messagebox.showerror(
                "Некорректные настройки Magic Print",
                str(exc) or "Проверьте числовые значения настроек симуляции.",
                parent=menu_win,
            )
            return

        sel = preset_var.get().strip()
        CONFIG["ACTIVE_PRESET"] = sel
        CONFIG["API_URL"] = url_entry.get().strip()
        
        current_model = model_entry.get().strip()
        current_key = key_entry.get().strip()
        
        CONFIG["MODEL"] = current_model
        CONFIG["API_KEY"] = current_key
        CONFIG["MODELS"][sel] = current_model
        CONFIG["API_KEYS"][sel] = current_key
        CONFIG["ACTIVE_THEME"] = theme_var.get()
        CONFIG["GLASS_BLUR"] = glass_blur_var.get()
        CONFIG["SYNC_PIXEL_THEME"] = sync_pixel_var.get()
        CONFIG["MAGIC_PRINT"].update(magic_values)
        CONFIG["MAGIC_PRINT"]["mode"] = selected_mode
        CONFIG["MAGIC_PRINT"]["skip_auto_indent"] = skip_auto_indent_var.get()

        for k, ent in hotkey_entries.items():
            val = ent.get().strip().lower()
            if val:
                CONFIG["HOTKEYS"][k] = val

        register_hotkeys()
        persist_runtime_settings()
        blink_pixel(get_color("ready"), count=1)
        _on_close()

    ttk.Button(btn_frame, text="💾 Сохранить и закрыть (Esc)", style="Primary.TButton", command=save_and_close).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(6, 0))

def register_hotkeys():
    try:
        keyboard.unhook_all_hotkeys()
    except Exception:
        pass

    hk = CONFIG["HOTKEYS"]
    action_map = {
        "send": on_send_hotkey,
        "magic_print": lambda: toggle_magic_mode(),
        "quick_insert": on_quick_insert,
        "clear_code": clear_generated_code,
        "add_context": on_add_context,
        "clear_context": clear_context_buffer,
        "retry": on_retry_hotkey,
        "menu": show_settings_menu,
        "panic_sleep": panic_sleep_toggle,
        "panic_kill": lambda: threading.Thread(target=panic_self_destruct, daemon=True).start(),
        "panic_kill_alt": lambda: threading.Thread(target=panic_self_destruct, daemon=True).start(),
    }

    for action_name, combo in hk.items():
        if combo and action_name in action_map:
            try:
                keyboard.add_hotkey(combo, action_map[action_name])
            except Exception as e:
                append_log(f"[WARN] Ошибка бинда '{combo}' для {action_name}: {e}")

def init_pixel_system():
    root = tk.Tk()
    state.root = root
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-toolwindow", True)
    root.geometry(f"{CONFIG['STATUS_PIXEL_SIZE']}{CONFIG['STATUS_PIXEL_POS']}")

    pixel = tk.Label(root, bg=get_color("idle"), bd=0)
    pixel.pack(fill=tk.BOTH, expand=True)
    state.pixel_label = pixel

    sw = root.winfo_screenwidth()
    bar_win = tk.Toplevel(root)
    state.bar_window = bar_win
    bar_win.overrideredirect(True)
    bar_win.attributes("-topmost", True)
    bar_win.attributes("-toolwindow", True)
    bar_win.configure(bg=get_color("idle"))
    bar_win.geometry(f"5x1+{sw - 6}+0")

    state.bar_labels = []
    for _ in range(CONFIG["BAR_PIXELS_COUNT"]):
        lbl = tk.Label(bar_win, bg=get_color("idle"), bd=0, width=1, height=1)
        lbl.pack(side=tk.LEFT)
        state.bar_labels.append(lbl)

    register_hotkeys()
    root.mainloop()

if __name__ == "__main__":
    init_pixel_system()