import os
import sys
import time
import re
import json
import threading
import subprocess
import tempfile
from typing import Optional, List, Tuple

import requests
import pyperclip
import keyboard
import tkinter as tk
from tkinter import ttk

CONFIG = {
    "ACTIVE_PRESET": "together",
    
    "API_URL": "https://api.together.ai/v1/chat/completions",
    "API_KEY": "key_CfWVeu9a6dKTddzQjVNz7",
    "MODEL": "Prism-ML/Ternary-Bonsai-27B",
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
        "gemini": "gemini-2.0-flash",
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
        "menu": "f8",
        "panic_sleep": "ctrl+left shift+f9",
        "panic_kill": "ctrl+left shift+f12",
        "panic_kill_alt": "ctrl+left shift+delete"
    },

    "COLORS": {
        "idle": "#18181b",
        "loading": "#38bdf8",
        "ready": "#4ade80",
        "orange": "#fb923c",
        "red": "#f87171",
        "error": "#f87171",
        "bar_active": "#991b1b",
    },

    "STATUS_PIXEL_SIZE": "2x2",
    "STATUS_PIXEL_POS": "+0+0",
    "BAR_PIXELS_COUNT": 5,
    "LOG_LIMIT": 15000,
    "MAGIC_CHUNK_SIZE": 1,
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

def persist_runtime_settings():
    def _clean(val):
        return str(val or "").replace("\\", "\\\\").replace('"', '\\"')

    try:
        script_path = os.path.abspath(__file__ if "__file__" in globals() else sys.argv[0])
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()

        for key in ["ACTIVE_PRESET", "API_URL", "MODEL", "API_KEY"]:
            pattern = rf'("{key}"\s*:\s*")[^"]*(")'
            content = re.sub(pattern, rf'\g<1>{_clean(CONFIG[key])}\g<2>', content, count=1)

        for block_name in ["API_KEYS", "MODELS", "HOTKEYS"]:
            m_block = re.search(rf'("{block_name}"\s*:\s*\{{[^}}]*\}})', content)
            if m_block:
                old_block = m_block.group(1)
                new_block = old_block
                for sub_k, sub_v in CONFIG[block_name].items():
                    sub_pat = rf'("{sub_k}"\s*:\s*")[^"]*(")'
                    new_block = re.sub(sub_pat, rf'\g<1>{_clean(sub_v)}\g<2>', new_block, count=1)
                content = content.replace(old_block, new_block, 1)

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(content)
        append_log("[CONFIG] Настройки и хоткеи успешно сохранены в файл.")
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
        append_log("[ОШИБКА] API Key пуст! Откройте настройки (Ctrl+Shift+F8) и введите ключ.")
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
        animate_magic_toggle(turn_on=True)
        append_log("[MAGIC] Магическая печать: ВКЛ.")
        rem = len(state.generated_code) - state.magic_index
        update_bar_display(rem)

        if state.magic_hook is None:
            state.magic_hook = keyboard.hook(magic_keyboard_hook, suppress=True)
    else:
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

def show_settings_menu():
    if state.is_sleeping or state.is_destroying:
        return

    if state.settings_window and state.settings_window.winfo_exists():
        state.settings_window.focus_force()
        return

    menu_win = tk.Toplevel(state.root)
    state.settings_window = menu_win
    menu_win.title("Core Settings")
    menu_win.geometry("740x680")
    menu_win.configure(bg="#18181b")
    menu_win.attributes("-topmost", True)
    menu_win.resizable(False, False)

    def _on_close():
        state.settings_window = None
        menu_win.destroy()

    menu_win.bind("<Escape>", lambda e: _on_close())
    menu_win.protocol("WM_DELETE_WINDOW", _on_close)

    style = ttk.Style(menu_win)
    style.theme_use("clam")
    style.configure(".", background="#18181b", foreground="#f4f4f5", font=("Segoe UI", 9))
    style.configure("TFrame", background="#18181b")
    style.configure("TLabel", background="#18181b", foreground="#e4e4e7")
    style.configure("Header.TLabel", font=("Segoe UI", 11, "bold"), foreground="#38bdf8")
    style.configure("Sub.TLabel", font=("Segoe UI", 9, "bold"), foreground="#a1a1aa")
    style.configure("Status.TLabel", font=("Segoe UI", 9, "bold"), foreground="#4ade80")
    style.configure("TEntry", fieldbackground="#27272a", foreground="#ffffff", insertcolor="#ffffff", borderwidth=0)
    style.configure("TCombobox", fieldbackground="#27272a", foreground="#ffffff", selectbackground="#3f3f46", borderwidth=0)
    style.map("TCombobox", fieldbackground=[("readonly", "#27272a")], selectbackground=[("readonly", "#3f3f46")])
    style.configure("Dark.TButton", background="#3f3f46", foreground="#ffffff", borderwidth=0, padding=5, font=("Segoe UI", 9, "bold"))
    style.map("Dark.TButton", background=[("active", "#52525b"), ("pressed", "#27272a")])

    notebook = ttk.Notebook(menu_win)
    notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

    tab_api = ttk.Frame(notebook, padding=12)
    tab_hotkeys = ttk.Frame(notebook, padding=12)
    notebook.add(tab_api, text=" Сервис и Модель ")
    notebook.add(tab_hotkeys, text=" Кастомные Хоткеи ")

    ttk.Label(tab_api, text="Конфигурация нейросети", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 8))

    ttk.Label(tab_api, text="Провайдер нейросети:").pack(anchor=tk.W, pady=(2, 2))
    preset_var = tk.StringVar(value=CONFIG["ACTIVE_PRESET"])
    preset_combo = ttk.Combobox(tab_api, textvariable=preset_var, state="readonly")
    preset_combo["values"] = list(API_PRESETS.keys())
    preset_combo.pack(fill=tk.X, pady=(0, 6))

    ttk.Label(tab_api, text="API URL:").pack(anchor=tk.W)
    url_entry = ttk.Entry(tab_api)
    url_entry.insert(0, CONFIG["API_URL"])
    url_entry.pack(fill=tk.X, pady=(0, 6))

    key_frame = ttk.Frame(tab_api)
    key_frame.pack(fill=tk.X, pady=(0, 2))
    ttk.Label(key_frame, text="API Key:").pack(side=tk.LEFT)
    
    show_key_var = tk.BooleanVar(value=False)
    def _toggle_key_vis():
        key_entry.configure(show="" if show_key_var.get() else "*")

    show_chk = ttk.Checkbutton(key_frame, text="Показать ключ", variable=show_key_var, command=_toggle_key_vis)
    show_chk.pack(side=tk.RIGHT)

    key_entry = ttk.Entry(tab_api, show="*")
    key_entry.insert(0, CONFIG["API_KEY"])
    key_entry.pack(fill=tk.X, pady=(0, 6))

    ttk.Label(tab_api, text="Имя модели:").pack(anchor=tk.W)
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

    ttk.Label(tab_api, text="Системный лог:").pack(anchor=tk.W)
    log_text = tk.Text(tab_api, height=6, wrap=tk.NONE, state="disabled", bg="#09090b", fg="#a1a1aa", insertbackground="#ffffff", bd=0, padx=8, pady=4, font=("Consolas", 8))
    state.log_widget = log_text
    
    log_scroll = ttk.Scrollbar(tab_api, orient=tk.VERTICAL, command=log_text.yview)
    log_text.configure(yscrollcommand=log_scroll.set)
    log_scroll.pack(fill=tk.Y, side=tk.RIGHT)
    log_text.pack(fill=tk.BOTH, expand=True, pady=(2, 6))

    ttk.Label(tab_hotkeys, text="Настройка клавиатурных комбинаций", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 10))
    
    hotkey_entries = {}
    hk_labels = {
        "send": "Запрос решения по выделению:",
        "magic_print": "Магическая печать (посимвольно):",
        "quick_insert": "Мгновенная вставка (Ctrl+V):",
        "clear_code": "Очистить буфер кода (Drop):",
        "add_context": "Добавить выделение в контекст:",
        "clear_context": "Очистить весь контекст:",
        "retry": "Повторить последнюю генерацию:",
        "menu": "Открыть это меню настроек:",
        "panic_sleep": "Анабиоз (сон) на 5 минут:",
        "panic_kill": "Экстренное стирание с диска:",
    }

    hk_grid = ttk.Frame(tab_hotkeys)
    hk_grid.pack(fill=tk.BOTH, expand=True)

    row_i = 0
    for key_name, label_text in hk_labels.items():
        ttk.Label(hk_grid, text=label_text).grid(row=row_i, column=0, sticky=tk.W, pady=3, padx=(0, 10))
        entry = ttk.Entry(hk_grid, width=28)
        entry.insert(0, CONFIG["HOTKEYS"].get(key_name, ""))
        entry.grid(row=row_i, column=1, sticky=tk.E, pady=3)
        hotkey_entries[key_name] = entry
        row_i += 1

    btn_frame = ttk.Frame(menu_win, padding=12)
    btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

    ttk.Button(btn_frame, text="⚡ Проверить связь с API", style="Dark.TButton", command=test_api_connection).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

    def save_and_close():
        sel = preset_var.get().strip()
        CONFIG["ACTIVE_PRESET"] = sel
        CONFIG["API_URL"] = url_entry.get().strip()
        
        current_model = model_entry.get().strip()
        current_key = key_entry.get().strip()
        
        CONFIG["MODEL"] = current_model
        CONFIG["API_KEY"] = current_key
        CONFIG["MODELS"][sel] = current_model
        CONFIG["API_KEYS"][sel] = current_key

        for k, ent in hotkey_entries.items():
            val = ent.get().strip().lower()
            if val:
                CONFIG["HOTKEYS"][k] = val

        register_hotkeys()
        persist_runtime_settings()
        blink_pixel(get_color("ready"), count=1)
        _on_close()

    ttk.Button(btn_frame, text="Сохранить и закрыть (Esc)", style="Dark.TButton", command=save_and_close).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(4, 0))

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